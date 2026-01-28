# -*- coding: utf-8 -*-

import asyncio
import logging
import random
from typing import Optional, Tuple, Any

from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)

class OkoooDownloader:
    """
    Okooo下载器
    负责页面HTML的下载，包含反爬处理和WAF检测
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        
    async def _create_browser_context(self) -> Tuple[Any, Browser, BrowserContext]:
        """
        创建Playwright浏览器上下文，注入反爬脚本
        """
        p = await async_playwright().start()
        
        args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
        
        browser = await p.chromium.launch(headless=self.headless, args=args)
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation'],
            geolocation={'latitude': 31.2304, 'longitude': 121.4737}, # Shanghai
            color_scheme='light'
        )
        
        # 注入反爬脚本
        await context.add_init_script("""
            // 1. Pass webdriver check
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 2. Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            
            // 3. Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 4. Mock chrome object
            window.chrome = {
                runtime: {}
            };
            
            // 5. Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: 'denied' }) :
                    originalQuery(parameters)
            );
        """)
        
        return p, browser, context

    def _is_blocked(self, content: str, title: str, current_url: str, target_url: str) -> bool:
        """
        检查是否被WAF拦截或软屏蔽
        """
        # 1. WAF indicators
        if "www.aliyun.com" in content or "405" in title or "您的访问被阻断" in content:
            logger.error("Detected WAF Block (Aliyun 405).")
            return True
            
        # 2. Soft block (redirect to homepage)
        # Note: target_url might be different if there were redirects, but here we compare with intended target
        # We assume target_url is the one we wanted to visit.
        if current_url == "https://www.okooo.com/" and target_url != "https://www.okooo.com/":
             logger.error("Redirected to homepage (Soft Block).")
             return True
             
        # 3. Content too short
        if len(content) < 1000:
            logger.warning("Content too short, possibly blocked or empty.")
            return True
            
        return False

    async def download_html(self, url: str) -> Optional[str]:
        """
        下载指定URL的HTML内容
        
        Args:
            url: 目标URL
            
        Returns:
            Optional[str]: 成功返回HTML内容，失败返回None
        """
        playwright = None
        browser = None
        context = None
        
        try:
            playwright, browser, context = await self._create_browser_context()
            
            # Randomize User Agent
            chrome_version = random.randint(115, 120)
            if self.is_mobile:
                ua = f"Mozilla/5.0 (iPhone; CPU iPhone OS 16_{random.randint(0, 6)} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
                sec_ch_ua_platform = '"iOS"'
                sec_ch_ua_mobile = "?1"
            else:
                ua = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
                sec_ch_ua_platform = '"macOS"'
                sec_ch_ua_mobile = "?0"
            
            # Enhanced Headers
            await context.set_extra_http_headers({
                "User-Agent": ua,
                "Referer": "https://www.okooo.com/",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Sec-Ch-Ua": f'"Not_A Brand";v="8", "Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}"',
                "Sec-Ch-Ua-Mobile": sec_ch_ua_mobile,
                "Sec-Ch-Ua-Platform": sec_ch_ua_platform,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            })
            
            page = await context.new_page()
            
            # 策略：先访问主页建立Session/Cookies
            try:
                # logger.info("Visiting homepage to establish session...")
                await page.goto("https://www.okooo.com/", wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(random.uniform(2, 4))
                
                # 模拟简单交互
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await page.evaluate("window.scrollTo(0, 200)")
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.warning(f"Homepage visit failed: {e}, continuing...")

            logger.info(f"Navigating to {url}")
            
            # Update Referer
            await page.set_extra_http_headers({
                "Referer": "https://www.okooo.com/",
            })

            # 访问目标页面
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=40000)
                
                if response and response.status == 405:
                    logger.error("Got 405 status code directly.")
                    return None
                    
            except Exception as e:
                logger.warning(f"Navigation warning: {e}, but continuing to check content...")

            await asyncio.sleep(random.uniform(4, 7)) # 等待动态内容加载
            
            # 模拟滚动
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/1.5)")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            content = await page.content()
            title = await page.title()
            current_url = page.url
            
            if self._is_blocked(content, title, current_url, url):
                return None
            
            logger.info(f"Download success. Title: {title}, Size: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return None
        finally:
            if context: await context.close()
            if browser: await browser.close()
            if playwright: await playwright.stop()
