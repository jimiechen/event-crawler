#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺 realhead API 爬虫
基于 Playwright 实现，支持 Cookie 注入和会话管理
"""

import re
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, BrowserContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler.base import CrawlerBase
from app.services.stock_service import StockService

logger = logging.getLogger(__name__)


class RealheadCrawler(CrawlerBase):
    """同花顺 realhead API 爬虫"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, 'tonghuashun')
        self.stock_service = StockService(db)
        
        # 字段映射（在爬虫中完成，减少维护量）
        self.FIELD_MAPPING = {
            "10": "current_price",
            "7": "open_price",
            "8": "high_price",
            "9": "low_price",
            "6": "prev_close",
            "13": "volume",
            "19": "turnover",
            "1968584": "turnover_rate",
            "5": "stock_code",
            "name": "stock_name",
            "199112": "change_percent"
        }
    
    async def crawl(self, stock_codes: List[str] = None) -> Dict[str, Any]:
        """
        抓取 realhead 数据
        :param stock_codes: 股票代码列表，如果为空则抓取所有自选股
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
            
            # 设置网络监听
            realhead_data = await self.intercept_realhead_requests(page, stock_codes)
            
            # 同步会话
            await self.sync_session(context, session)
            
            return {
                "status": "success",
                "data": realhead_data,
                "count": len(realhead_data)
            }
            
        except Exception as e:
            logger.error(f"抓取失败: {e}")
            raise e
        finally:
            if context:
                await context.close()
            if browser:
                await browser.close()
    
    async def intercept_realhead_requests(self, page: Page, stock_codes: List[str] = None) -> List[Dict[str, Any]]:
        """
        拦截 realhead API 请求
        """
        realhead_data = []
        captured_requests = set()
        
        async def handle_route(route, request):
            url = request.url
            if 'v2/realhead/hs_' in url:
                # 获取响应
                response = await route.fetch()
                text = await response.text()
                
                # 解析 JSONP
                parsed_data = self.parse_realhead_jsonp(text)
                if parsed_data:
                    # 转换字段（在爬虫中完成）
                    converted_data = self.convert_fields(parsed_data)
                    realhead_data.append(converted_data)
                    captured_requests.add(url)
                    logger.info(f"成功解析股票数据: {converted_data.get('stock_code')}")
                
                # 继续路由
                await route.fulfill(response=response)
            else:
                await route.continue_()
        
        # 注册路由
        await page.route('**/*', handle_route)
        
        # 访问同花顺页面
        if stock_codes:
            # 访问指定股票页面
            for code in stock_codes:
                url = f"http://stockpage.10jqka.com.cn/{code}"
                logger.info(f"访问股票页面: {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)  # 等待 realhead 请求
        else:
            # 访问自选股页面
            logger.info("访问自选股页面")
            await page.goto("https://t.10jqka.com.cn/newcircle/user/userPersonal/?from=finance&tab=zx", 
                          wait_until='networkidle', timeout=30000)
            await asyncio.sleep(5)  # 等待所有 realhead 请求
        
        logger.info(f"共捕获 {len(realhead_data)} 条 realhead 数据")
        return realhead_data
    
    def parse_realhead_jsonp(self, jsonp_text: str) -> Optional[Dict[str, Any]]:
        """
        解析 realhead JSONP 响应
        """
        try:
            # 提取 JSONP 中的 JSON 数据
            pattern = r'quotebridge_v2_realhead_hs_(\d+)_last\s*\(\s*(\{.*\})\s*\)'
            match = re.search(pattern, jsonp_text)
            
            if match and match.group(2):
                return json.loads(match.group(2))
            
            logger.warning(f"JSONP 解析失败: {jsonp_text[:100]}")
            return None
            
        except Exception as e:
            logger.error(f"JSONP 解析异常: {e}")
            return None
    
    def convert_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换字段（在爬虫中完成，减少维护量）
        """
        converted = {}
        
        # 合并 items 中的字段到主字典
        if 'items' in raw_data:
            raw_data = {**raw_data, **raw_data['items']}
        
        for field_id, value in raw_data.items():
            # 跳过 items 字段
            if field_id == 'items':
                continue
                
            field_name = self.FIELD_MAPPING.get(field_id)
            
            if field_name:
                # 转换数据类型
                if field_name in ['volume']:
                    converted[field_name] = int(float(value)) if value else 0
                elif field_name in ['current_price', 'open_price', 'high_price', 'low_price', 
                                    'prev_close', 'turnover', 'change_percent', 'turnover_rate']:
                    converted[field_name] = float(value) if value else 0.0
                else:
                    converted[field_name] = str(value) if value else ''
        
        # 添加时间戳
        converted['request_timestamp'] = datetime.now().isoformat()
        converted['timestamp'] = datetime.now().date().isoformat()
        
        return converted
    
    async def check_login_status(self, url: str = None, nickname_xpath: str = None) -> Dict[str, Any]:
        """
        检查同花顺登录状态
        """
        context = None
        session = None
        browser = None
        
        try:
            platform_config = await self.get_platform_config()
            if not platform_config:
                return {"logged_in": False, "message": "平台配置不存在"}
            
            verify_api = platform_config.get('verify_api')
            verify_type = platform_config.get('verify_type', 'json')
            verify_xpath = platform_config.get('verify_xpath')
            verify_parser = platform_config.get('verify_parser')
            
            if not verify_api:
                return {"logged_in": False, "message": "未配置验证接口"}
            
            # 创建浏览器上下文
            context, session, browser = await self.create_browser_context()
            page = await context.new_page()
            
            try:
                # 访问验证接口
                await page.goto(verify_api, wait_until='networkidle', timeout=30000)
                
                # 根据验证类型提取账号信息
                account_name = None
                
                if verify_type == 'json':
                    # JSON方式验证
                    content = await page.content()
                    json_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            if verify_parser:
                                parser_config = json.loads(verify_parser)
                                path = parser_config.get('path', '')
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
                
                elif verify_type == 'dom' and verify_xpath:
                    # XPath方式验证
                    element = await page.query_selector(verify_xpath)
                    if element:
                        account_name = await element.inner_text()
                
                # 如果提供了昵称 XPath，使用它来检查
                if nickname_xpath and not account_name:
                    element = await page.query_selector(nickname_xpath)
                    if element:
                        account_name = await element.inner_text()
                
                # 判断登录状态
                if account_name:
                    # 更新会话验证状态
                    if session and session.get('id'):
                        await self.session_service.verify_session(session['id'], True)
                    
                    return {
                        "logged_in": True,
                        "message": "登录成功",
                        "nickname": account_name
                    }
                else:
                    # 更新会话验证状态
                    if session and session.get('id'):
                        await self.session_service.verify_session(session['id'], False)
                    
                    return {
                        "logged_in": False,
                        "message": "未检测到登录状态",
                        "need_xpath": True
                    }
            
            except Exception as e:
                logger.error(f"登录状态检查失败: {e}")
                return {
                    "logged_in": False,
                    "message": f"检查失败: {str(e)}"
                }
            finally:
                if browser:
                    await browser.close()
        
        except Exception as e:
            logger.error(f"登录状态检查异常: {e}")
            return {
                "logged_in": False,
                "message": f"检查异常: {str(e)}"
            }
