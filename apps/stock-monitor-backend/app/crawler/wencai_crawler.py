#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财自动爬虫
基于Playwright实现，支持Cookie注入和自动翻页
"""

import asyncio
import logging
import json
import random
import re
import time
import os
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import date as datetime_date
from playwright.async_api import async_playwright, Page, BrowserContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.wencai_service import WencaiService
from app.crawler.base import CrawlerBase

logger = logging.getLogger(__name__)

class WencaiCrawler(CrawlerBase):
    def __init__(self, db: AsyncSession):
        super().__init__(db, 'wencai')
        self.wencai_service = WencaiService(db)
        # 使用PC版搜索页面，通常结构更稳定且是表格形式
        self.base_url = "http://www.iwencai.com/stockpick/search"
    
    async def crawl(self, *args, **kwargs) -> Dict[str, Any]:
        """
        爬取方法（实现基类抽象方法）
        """
        # WencaiCrawler使用fetch_and_parse方法，这里只是满足基类要求
        return await self.fetch_and_parse(*args, **kwargs)

    async def fetch_and_parse(self, query: str, batch_name: str = None, target_stock_code: str = None, debug_url: str = None, target_date: datetime_date = None) -> Dict[str, Any]:
        """
        执行抓取并解析
        :param query: 搜索条件
        :param batch_name: 批次名称
        :param target_stock_code: 目标股票代码，如果提供则校验该股票是否存在于结果中
        :param debug_url: 调试URL，如果提供则直接访问该URL而不是生成查询URL
        :param target_date: 目标日期，用于生成特定日期的查询
        """
        html_content = await self.fetch_page_source(query, debug_url=debug_url)
        
        if not html_content:
            logger.error("Failed to fetch page content")
            return {"status": "failed", "error": "Fetch failed"}

        # 创建批次
        if not batch_name:
            import datetime
            batch_name = f"AutoCrawl_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        batch_id = await self.wencai_service.create_crawl_batch(
            batch_name=batch_name,
            crawl_url=f"{self.base_url}?w={query}",
            query_string=query
        )

        # 解析
        parsed_stocks = self.wencai_service.parse_html_table(html_content, debug=True)
        
        if parsed_stocks:
            logger.info(f"Parsed {len(parsed_stocks)} stocks. Saving to database...")
            # 传递 target_date 给 save_stocks 以便正确计算该日期的分数
            if target_date:
                for stock in parsed_stocks:
                    stock['date'] = target_date
            
            await self.wencai_service.save_stocks(parsed_stocks, batch_id)
        
        if not parsed_stocks:
            # Save HTML for debugging
            try:
                with open("debug_wencai.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Saved failed HTML to debug_wencai.html")
            except Exception as e:
                logger.error(f"Failed to save debug HTML: {e}")

            # Even if no stocks parsed, we consider it "completed" (just empty result)
            # This allows the user to see that 0 stocks were found, rather than a generic error.
            # But we log a warning.
            logger.warning("No stocks parsed from page content. Possibly no results or layout changed.")
            
            # await self.wencai_service.update_batch_status(batch_id, 'failed', 0, 0, 0, 'No data parsed')
            # return {"status": "failed", "error": "No data parsed"}
            
        # 校验目标股票是否存在
        found_target = False
        if target_stock_code:
            logger.info(f"Validating target stock: {target_stock_code}")
            # 格式化 target_stock_code，确保匹配 (例如 000001.SZ vs 000001)
            target_short = target_stock_code.split('.')[0]
            for stock in parsed_stocks:
                stock_code = stock.get('stock_code', '')
                if target_short in stock_code:
                    found_target = True
                    logger.info(f"Target stock found! {target_stock_code} matched with {stock_code}")
                    break
            
            if not found_target:
                logger.warning(f"Target stock {target_stock_code} not found in crawler results")
                # 虽然没找到目标股票，但爬虫数据还是可以保存
        
        # 保存
        success, failed, errors = await self.wencai_service.save_wencai_stocks(batch_id, parsed_stocks)
        
        # 处理后续 (标签等)
        await self.wencai_service.process_batch_data(batch_id)
        
        # 更新状态
        # Even if 0 stocks found (success=0), if parsed_stocks was empty, it's a valid "completed" (just no results)
        status = 'completed' if (success > 0 or len(parsed_stocks) == 0) else 'failed'
        await self.wencai_service.update_batch_status(
            batch_id, status, len(parsed_stocks), success, failed, str(errors)
        )
        
        return {
            "status": status,
            "batch_id": batch_id,
            "total": len(parsed_stocks),
            "success": success,
            "errors": errors,  # Return errors for debugging
            "found_target": found_target if target_stock_code else None,
            "stocks": parsed_stocks
        }

    async def fetch_page_source(self, query: str, debug_url: str = None) -> Optional[str]:
        """
        使用Playwright获取页面源码，支持WAP版和PC版自动切换
        :param query: 搜索条件
        :param debug_url: 调试URL，如果提供则直接访问该URL
        """
        context = None
        browser = None
        
        try:
            # 使用基类方法创建浏览器上下文
            context, session, browser = await self.create_browser_context()
            page = await context.new_page()
            
            # 打印当前Cookie信息（调试功能）
            cookies = await context.cookies()
            logger.info(f"========== 调试信息：当前Cookie ==========")
            for cookie in cookies:
                logger.info(f"  {cookie['name']}: {cookie['value'][:50]}..." if len(cookie['value']) > 50 else f"  {cookie['name']}: {cookie['value']}")
            logger.info(f"========== 共 {len(cookies)} 个Cookie ==========")
            
            # 如果提供了debug_url，直接访问
            if debug_url:
                logger.info(f"使用调试URL: {debug_url}")
                await page.goto(debug_url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(5)
                
                # 生成截图
                screenshot_path = f"debug_wencai_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"截图已保存到: {screenshot_path}")
                
                content = await page.content()
                await self.sync_session(context, session)
                return content
            
            # 优先尝试WAP版
            encoded_query = urllib.parse.quote(query)
            wap_url = f"https://www.iwencai.com/unifiedwap/result?w={encoded_query}"
            logger.info(f"Navigating to WAP URL: {wap_url}")
            
            try:
                await page.goto(wap_url, wait_until='networkidle', timeout=30000)
                # WAP版通常是动态加载，等待一段时间
                await asyncio.sleep(5)
                
                content = await page.content()
                
                # 检查WAP版是否有效（通过是否存在特定元素或反爬特征）
                # 假设WAP版成功加载会有内容，如果被拦截会有验证码
                if "验证码" not in content and "robot" not in content.lower():
                    logger.info("WAP version loaded successfully")
                    
                    # 生成截图
                    screenshot_name = f"debug_wencai_wap_{int(time.time())}.png"
                    screenshot_path = os.path.abspath(screenshot_name)
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"WAP版截图已保存到: {screenshot_path}")
                    
                    await self.sync_session(context, session)
                    return content
                else:
                    logger.warning("WAP版遭遇反爬，尝试切换PC版...")
            except Exception as e:
                logger.warning(f"WAP版访问失败: {e}，尝试切换PC版...")
            
            # 失败后尝试PC版
            pc_url = f"http://www.iwencai.com/stockpick/search?w={encoded_query}"
            logger.info(f"Navigating to PC URL: {pc_url}")
            
            await page.goto(pc_url, wait_until='networkidle', timeout=30000)
            
            # 等待表格加载
            try:
                # 尝试等待常见的表格选择器
                selectors = ['table', '.iwc-table-body', '.static_table', '.tib-table', '.wencai-table']
                
                # 轮询检查选择器
                found_selector = False
                for _ in range(20): # 20 * 0.5s = 10s
                    for selector in selectors:
                        if await page.query_selector(selector):
                            logger.info(f"Found table selector: {selector}")
                            found_selector = True
                            break
                    if found_selector:
                        break
                    await asyncio.sleep(0.5)
                    
                if not found_selector:
                    logger.warning("No standard table selector found, waiting a bit more...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.warning(f"Wait for selector failed: {e}")
                await asyncio.sleep(5)
            
            # 获取内容
            content = await page.content()
            
            # 生成截图
            screenshot_name = f"debug_wencai_pc_{int(time.time())}.png"
            screenshot_path = os.path.abspath(screenshot_name)
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"PC版截图已保存到: {screenshot_path}")
            
            # 简单的反爬检查
            if "robot" in content.lower() or "验证码" in content:
                logger.warning("Detected anti-crawler mechanism")
                logger.debug(f"Anti-crawler content snippet: {content[:500]}")
                return None
            
            # 同步最新的Cookies回数据库
            await self.sync_session(context, session)

            return content
            
        except Exception as e:
            logger.error(f"Playwright error: {e}")
            return None
        finally:
            # 清理资源
            if context:
                await context.close()
            if browser:
                await browser.close()
    
    async def check_login_status(self, url: str = None, nickname_xpath: str = None) -> Dict[str, Any]:
        """
        检查问财登录状态
        """
        context = None
        session = None
        browser = None
        
        try:
            platform_config = await self.get_platform_config()
            if not platform_config:
                return {"logged_in": False, "message": "平台配置不存在"}
            
            verify_api = platform_config.get('verify_api')
            verify_type = platform_config.get('verify_type', 'dom')
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

