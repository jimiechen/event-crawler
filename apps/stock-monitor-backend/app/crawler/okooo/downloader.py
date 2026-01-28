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
    
    def __init__(self, headless: bool = True, is_mobile: bool = False, storage_state_path: Optional[str] = None):
        self.headless = headless
        self.is_mobile = is_mobile
        self.storage_state_path = storage_state_path
        self.playwright = None
        self.browser = None
        self.context = None

    async def close(self):
        """关闭资源"""
        if self.context:
            try:
                if self.storage_state_path:
                    await self.context.storage_state(path=self.storage_state_path)
                await self.context.close()
            except Exception as e:
                logger.error(f"Error closing context: {e}")
            self.context = None
            
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def _ensure_context(self):
        """Ensure browser context exists"""
        if not self.playwright:
            self.playwright, self.browser, self.context = await self._create_browser_context()
        elif not self.browser:
            self.playwright, self.browser, self.context = await self._create_browser_context()
        elif not self.context:
            self.context = await self._create_context(self.browser)

    async def download(self, url: str) -> Optional[str]:
        """别名方法"""
        return await self.download_html(url)
    
    async def download_html(self, url: str) -> Optional[str]:
        """
        下载HTML内容
        """
        page = None
        try:
            await self._ensure_context()
            
            # Create new page in the persistent context
            page = await self.context.new_page()
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                # Wait for some content
                await page.wait_for_timeout(random.randint(1500, 3000))
                
                content = await page.content()
                title = await page.title()
                
                # Check for blocking
                if self._is_blocked(content, title, page.url, url):
                    logger.warning(f"Blocked or empty content for {url}")
                    return None
                
                # Save storage state periodically or on success
                if self.storage_state_path and self.context:
                    try:
                        await self.context.storage_state(path=self.storage_state_path)
                    except Exception as e:
                        logger.warning(f"Failed to save storage state: {e}")
                
                return content
                
            except Exception as e:
                logger.error(f"Page goto error for {url}: {e}")
                return None
            finally:
                if page:
                    await page.close()
            
        except Exception as e:
            logger.error(f"Download error for {url}: {e}")
            return None

    async def _create_context(self, browser: Browser) -> BrowserContext:
        """Create context with config"""
        if self.is_mobile:
            viewport = {'width': 375, 'height': 812}
            user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
            is_mobile_device = True
            sec_ch_ua_platform = '"iOS"'
            sec_ch_ua_mobile = "?1"
        else:
            viewport = {'width': 1920, 'height': 1080}
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            is_mobile_device = False
            sec_ch_ua_platform = '"macOS"'
            sec_ch_ua_mobile = "?0"
            
        context = await browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            is_mobile=is_mobile_device,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation'],
            geolocation={'latitude': 31.2304, 'longitude': 121.4737},
            color_scheme='light',
            storage_state=self.storage_state_path if self.storage_state_path else None
        )
        
        # Set extra headers globally for the context
        await context.set_extra_http_headers({
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Ch-Ua-Mobile": sec_ch_ua_mobile,
            "Sec-Ch-Ua-Platform": sec_ch_ua_platform,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })
        
        return context

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
        
        # Launch browser (headless handled here)
        browser = await p.chromium.launch(headless=self.headless, args=args)
        context = await self._create_context(browser)
        
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
        if current_url == "https://www.okooo.com/" and target_url != "https://www.okooo.com/":
             logger.error("Redirected to homepage (Soft Block).")
             return True
             
        # 3. Content too short
        if len(content) < 1000:
            logger.warning("Content too short, possibly blocked or empty.")
            return True
            
        return False
