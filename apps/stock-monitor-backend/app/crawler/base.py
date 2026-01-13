#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫基类
提供统一的会话管理和Cookie注入功能
"""

import json
import logging
import random
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page, BrowserContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.session_service import SessionService
from app.services.platform_service import PlatformService

logger = logging.getLogger(__name__)


class CrawlerBase(ABC):
    """爬虫基类"""

    def __init__(self, db: AsyncSession, platform_id: str):
        """
        初始化爬虫基类
        :param db: 数据库会话
        :param platform_id: 平台标识
        """
        self.db = db
        self.platform_id = platform_id
        self.session_service = SessionService(db)
        self.platform_service = PlatformService(db)
        self._platform_config = None
        self._current_session = None

    async def get_platform_config(self) -> Optional[Dict[str, Any]]:
        """获取平台配置"""
        if self._platform_config is None:
            self._platform_config = await self.platform_service.get_platform_by_id(self.platform_id)
        return self._platform_config

    async def get_best_session(self) -> Optional[Dict[str, Any]]:
        """获取最佳会话"""
        if self._current_session is None:
            self._current_session = await self.session_service.get_best_session(self.platform_id)
        return self._current_session

    async def create_browser_context(self) -> tuple[BrowserContext, Optional[Dict[str, Any]]]:
        """
        创建浏览器上下文并注入会话
        :return: (context, session)
        """
        platform_config = await self.get_platform_config()
        if not platform_config:
            raise ValueError(f"平台配置不存在: {self.platform_id}")

        p = await async_playwright().start()
        
        # 启动浏览器
        args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--window-size=1920,1080'
        ]
        browser = await p.chromium.launch(headless=True, args=args)
        
        # 创建上下文
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai'
        )
        
        # 添加反爬脚本
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # 注入会话
        session = await self.get_best_session()
        if session and session.get('cookies_json'):
            cookies = session['cookies_json']
            formatted_cookies = []
            for c in cookies:
                if 'name' in c and 'value' in c:
                    fc = {
                        'name': c['name'],
                        'value': c['value'],
                        'domain': c.get('domain', platform_config.get('domain', '')),
                        'path': c.get('path', '/')
                    }
                    formatted_cookies.append(fc)
            
            if formatted_cookies:
                await context.add_cookies(formatted_cookies)
                logger.info(f"注入 {len(formatted_cookies)} 个Cookie")
        
        return context, session, browser

    async def verify_session(self, page: Page, session: Optional[Dict[str, Any]]) -> bool:
        """
        验证会话是否有效
        :param page: 页面对象
        :param session: 会话信息
        :return: 是否验证成功
        """
        if not session:
            return False
        
        platform_config = await self.get_platform_config()
        if not platform_config:
            return False
        
        verify_api = platform_config.get('verify_api')
        verify_type = platform_config.get('verify_type', 'json')
        verify_xpath = platform_config.get('verify_xpath')
        verify_parser = platform_config.get('verify_parser')
        
        if not verify_api:
            logger.warning(f"平台 {self.platform_id} 未配置验证接口")
            return True
        
        try:
            # 访问验证接口
            await page.goto(verify_api, wait_until='networkidle', timeout=30000)
            
            # 根据验证类型提取账号信息
            account_name = None
            
            if verify_type == 'json':
                # JSON方式验证
                content = await page.content()
                # 尝试从页面中提取JSON数据
                import re
                json_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        if verify_parser:
                            parser_config = json.loads(verify_parser)
                            path = parser_config.get('path', '')
                            # 简单的JSON路径解析
                            keys = path.replace('$', '').split('.')
                            for key in keys:
                                if isinstance(data, dict):
                                    data = data.get(key)
                                elif isinstance(data, list) and key.isdigit():
                                    data = data[int(key)]
                                else:
                                    data = None
                                    break
                            if data:
                                account_name = str(data)
                    except Exception as e:
                        logger.warning(f"JSON解析失败: {e}")
            
            elif verify_type == 'text' and verify_xpath:
                # XPath方式验证
                element = await page.query_selector(verify_xpath)
                if element:
                    content = await element.inner_text()
                    if verify_parser:
                        parser_config = json.loads(verify_parser)
                        extract_field = parser_config.get('extract', '')
                        if extract_field:
                            # 简单的字段提取
                            import re
                            match = re.search(extract_field, content)
                            if match:
                                account_name = match.group(1) if match.groups() else match.group(0)
                    else:
                        account_name = content
            
            # 更新会话验证状态
            if session and session.get('id'):
                success = account_name is not None
                await self.session_service.verify_session(session['id'], success)
                
                if success:
                    logger.info(f"会话验证成功，账号: {account_name}")
                else:
                    logger.warning(f"会话验证失败")
                
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"会话验证异常: {e}")
            if session and session.get('id'):
                await self.session_service.verify_session(session['id'], False)
            return False

    async def sync_session(self, context: BrowserContext, session: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        同步会话Cookie回数据库
        :param context: 浏览器上下文
        :param session: 当前会话
        :return: 更新后的会话信息
        """
        try:
            cookies = await context.cookies()
            if not cookies:
                return session
            
            # 转换Cookie格式
            formatted_cookies = []
            for c in cookies:
                formatted_cookies.append({
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c["domain"],
                    "path": c["path"]
                })
            
            # 更新会话
            if session:
                await self.session_service.upsert_session(
                    platform_id=self.platform_id,
                    user_id=session['user_id'],
                    account_name=session.get('account_name', session['user_id']),
                    cookies=formatted_cookies
                )
                logger.info(f"同步 {len(formatted_cookies)} 个Cookie到数据库")
            
            return session
            
        except Exception as e:
            logger.error(f"同步会话失败: {e}")
            return session

    @abstractmethod
    async def crawl(self, *args, **kwargs) -> Dict[str, Any]:
        """
        爬取方法（子类实现）
        :return: 爬取结果
        """
        pass

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        执行爬取流程
        :return: 爬取结果
        """
        context = None
        browser = None
        session = None
        
        try:
            # 创建浏览器上下文
            context, session, browser = await self.create_browser_context()
            
            # 创建页面
            page = await context.new_page()
            
            # 验证会话
            await self.verify_session(page, session)
            
            # 执行爬取
            result = await self.crawl(page, *args, **kwargs)
            
            # 同步会话
            await self.sync_session(context, session)
            
            return result
            
        except Exception as e:
            logger.error(f"爬取失败: {e}")
            # 验证失败
            if session and session.get('id'):
                await self.session_service.verify_session(session['id'], False)
            raise e
            
        finally:
            # 清理资源
            if context:
                await context.close()
            if browser:
                await browser.close()
