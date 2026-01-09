#!/usr/bin/env python3
import asyncio
import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger


class BrowserManager:
    def __init__(
        self,
        extension_path: str,
        headless: bool = True,
        user_data_dir: Optional[str] = None
    ):
        self.extension_path = Path(extension_path)
        self.headless = headless
        self.user_data_dir = user_data_dir
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.pages: Dict[str, Page] = {}
        
        self.os_type = platform.system()
        self.is_windows = self.os_type == 'Windows'
        self.is_macos = self.os_type == 'Darwin'
        self.is_linux = self.os_type == 'Linux'
        
        logger.info(f"BrowserManager initialized with extension: {self.extension_path}")
    
    async def initialize(self):
        logger.info("Initializing browser manager...")
        
        self.playwright = await async_playwright().start()
        
        launch_args = self._get_launch_args()
        
        try:
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            logger.info("Browser launched successfully")
            
            await self._create_context()
            logger.info("Browser context created successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _get_launch_args(self) -> list:
        args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
        
        if self.extension_path.exists():
            args.append(f'--load-extension={self.extension_path}')
            logger.info(f"Loading extension from: {self.extension_path}")
        else:
            logger.warning(f"Extension path not found: {self.extension_path}")
        
        if self.user_data_dir:
            args.append(f'--user-data-dir={self.user_data_dir}')
            logger.info(f"Using user data directory: {self.user_data_dir}")
        
        return args
    
    async def _create_context(self):
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': self._get_user_agent(),
            'locale': 'zh-CN',
            'timezone_id': 'Asia/Shanghai',
            'ignore_https_errors': True,
        }
        
        if self.user_data_dir:
            context_options['storage_state'] = self.user_data_dir
        
        self.context = await self.browser.new_context(**context_options)
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
        """)
        
        logger.info("Browser context configured")
    
    def _get_user_agent(self) -> str:
        if self.is_windows:
            return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        elif self.is_macos:
            return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        else:
            return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    async def create_page(self, page_id: str = 'default') -> Page:
        if page_id in self.pages:
            logger.warning(f"Page {page_id} already exists, returning existing page")
            return self.pages[page_id]
        
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        page = await self.context.new_page()
        self.pages[page_id] = page
        
        logger.info(f"Created new page: {page_id}")
        return page
    
    async def get_page(self, page_id: str = 'default') -> Optional[Page]:
        return self.pages.get(page_id)
    
    async def close_page(self, page_id: str):
        if page_id in self.pages:
            await self.pages[page_id].close()
            del self.pages[page_id]
            logger.info(f"Closed page: {page_id}")
    
    async def navigate(self, url: str, page_id: str = 'default', wait_until: str = 'networkidle'):
        page = await self.get_page(page_id)
        if not page:
            page = await self.create_page(page_id)
        
        logger.info(f"Navigating to: {url}")
        await page.goto(url, wait_until=wait_until, timeout=30000)
        logger.info(f"Navigation completed: {url}")
    
    async def screenshot(self, page_id: str = 'default', path: Optional[str] = None) -> bytes:
        page = await self.get_page(page_id)
        if not page:
            raise RuntimeError(f"Page {page_id} not found")
        
        screenshot = await page.screenshot(full_page=True)
        logger.info(f"Screenshot taken for page: {page_id}")
        
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'wb') as f:
                f.write(screenshot)
            logger.info(f"Screenshot saved to: {path}")
        
        return screenshot
    
    async def execute_script(self, script: str, page_id: str = 'default', *args) -> Any:
        page = await self.get_page(page_id)
        if not page:
            raise RuntimeError(f"Page {page_id} not found")
        
        result = await page.evaluate(script, *args)
        logger.info(f"Script executed on page: {page_id}")
        return result
    
    async def click(self, selector: str, page_id: str = 'default'):
        page = await self.get_page(page_id)
        if not page:
            raise RuntimeError(f"Page {page_id} not found")
        
        await page.click(selector)
        logger.info(f"Clicked element: {selector}")
    
    async def fill(self, selector: str, value: str, page_id: str = 'default'):
        page = await self.get_page(page_id)
        if not page:
            raise RuntimeError(f"Page {page_id} not found")
        
        await page.fill(selector, value)
        logger.info(f"Filled element: {selector} with value: {value}")
    
    async def get_content(self, page_id: str = 'default') -> str:
        page = await self.get_page(page_id)
        if not page:
            raise RuntimeError(f"Page {page_id} not found")
        
        content = await page.content()
        logger.info(f"Retrieved content from page: {page_id}")
        return content
    
    async def wait_for_selector(self, selector: str, page_id: str = 'default', timeout: int = 30000):
        page = await self.get_page(page_id)
        if not page:
            raise RuntimeError(f"Page {page_id} not found")
        
        await page.wait_for_selector(selector, timeout=timeout)
        logger.info(f"Selector found: {selector}")
    
    async def wait_for_load_state(self, page_id: str = 'default', state: str = 'networkidle'):
        page = await self.get_page(page_id)
        if not page:
            raise RuntimeError(f"Page {page_id} not found")
        
        await page.wait_for_load_state(state)
        logger.info(f"Load state reached: {state}")
    
    async def get_cookies(self, page_id: str = 'default') -> list:
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        cookies = await self.context.cookies()
        logger.info(f"Retrieved {len(cookies)} cookies")
        return cookies
    
    async def set_cookies(self, cookies: list):
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        await self.context.add_cookies(cookies)
        logger.info(f"Set {len(cookies)} cookies")
    
    async def close(self):
        logger.info("Closing browser manager...")
        
        for page_id, page in self.pages.items():
            try:
                await page.close()
                logger.info(f"Closed page: {page_id}")
            except Exception as e:
                logger.error(f"Error closing page {page_id}: {e}")
        
        self.pages.clear()
        
        if self.context:
            try:
                await self.context.close()
                logger.info("Browser context closed")
            except Exception as e:
                logger.error(f"Error closing context: {e}")
        
        if self.browser:
            try:
                await self.browser.close()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
        
        if self.playwright:
            try:
                await self.playwright.stop()
                logger.info("Playwright stopped")
            except Exception as e:
                logger.error(f"Error stopping playwright: {e}")
        
        logger.info("Browser manager closed")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()