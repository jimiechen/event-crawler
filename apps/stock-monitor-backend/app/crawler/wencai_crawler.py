#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财自动爬虫
基于Playwright实现，支持Cookie注入和自动翻页
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, BrowserContext
from app.services.cookie_service import CookieService
from app.services.wencai_service import WencaiService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class WencaiCrawler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cookie_service = CookieService(db)
        self.wencai_service = WencaiService(db)
        # 使用PC版搜索页面，通常结构更稳定且是表格形式
        self.base_url = "http://www.iwencai.com/stockpick/search"

    async def fetch_and_parse(self, query: str, batch_name: str = None, target_stock_code: str = None) -> Dict[str, Any]:
        """
        执行抓取并解析
        :param query: 搜索条件
        :param batch_name: 批次名称
        :param target_stock_code: 目标股票代码，如果提供则校验该股票是否存在于结果中
        """
        html_content = await self.fetch_page_source(query)
        
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
            "found_target": found_target if target_stock_code else None,
            "stocks": parsed_stocks
        }

    async def fetch_page_source(self, query: str) -> Optional[str]:
        """
        使用Playwright获取页面源码
        """
        async with async_playwright() as p:
            # 启动浏览器 (headless=True)
            # 添加反爬参数
            args = [
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--window-size=1920,1080'
            ]
            browser = await p.chromium.launch(headless=True, args=args)
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            # 注入Cookies
            await self._inject_cookies(context)
            
            # 添加更多反爬脚本
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await context.new_page()
            
            try:
                # 构建URL
                url = f"{self.base_url}?w={query}"
                logger.info(f"Navigating to: {url}")
                
                # 访问页面
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                # 等待表格加载
                try:
                    # 尝试等待常见的表格选择器
                    # 问财的表格经常变，这里尝试几个可能的选择器
                    # table: 标准表格
                    # .iwc-table-body: 新版div表格
                    # .static_table: 另一种可能的类名
                    # .tib-table: 同花顺可能使用的类名
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
                
                # 简单的反爬检查 (如果内容太短或者包含特定验证码提示)
                if "robot" in content.lower() or "验证码" in content:
                    logger.warning("Detected anti-crawler mechanism")
                    # 记录一小段内容以便调试
                    logger.debug(f"Anti-crawler content snippet: {content[:500]}")
                    return None
                
                # 同步最新的Cookies回数据库
                await self._save_cookies_from_context(context, "iwencai.com")

                return content
                
            except Exception as e:
                logger.error(f"Playwright error: {e}")
                return None
            finally:
                await context.close()
                await browser.close()

    async def _save_cookies_from_context(self, context: BrowserContext, domain: str):
        """从Playwright上下文保存Cookies回数据库"""
        try:
            cookies = await context.cookies()
            if cookies:
                # 转换Playwright cookie格式为通用格式
                formatted_cookies = []
                for c in cookies:
                    formatted_cookies.append({
                        "name": c["name"],
                        "value": c["value"],
                        "domain": c["domain"],
                        "path": c["path"]
                    })
                
                await self.cookie_service.sync_cookies(domain, formatted_cookies)
                logger.info(f"Synced {len(formatted_cookies)} cookies back to DB for {domain}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    async def _inject_cookies(self, context: BrowserContext):
        """注入Cookies"""
        try:
            # 获取 iwencai.com 的 cookies
            cookies = await self.cookie_service.get_cookies("iwencai.com")
            if not cookies:
                # 尝试主域名
                cookies = await self.cookie_service.get_cookies("10jqka.com.cn")
            
            if cookies:
                # Playwright cookie format might differ slightly, ensure compatibility
                formatted_cookies = []
                for c in cookies:
                    # Playwright needs 'name', 'value', 'domain', 'path'
                    if 'name' in c and 'value' in c:
                        fc = {
                            'name': c['name'],
                            'value': c['value'],
                            'domain': c.get('domain', '.iwencai.com'),
                            'path': c.get('path', '/')
                        }
                        formatted_cookies.append(fc)
                
                if formatted_cookies:
                    await context.add_cookies(formatted_cookies)
                    logger.info(f"Injected {len(formatted_cookies)} cookies")
            else:
                logger.warning("No cookies found for iwencai/10jqka")
        except Exception as e:
            logger.error(f"Cookie injection failed: {e}")

