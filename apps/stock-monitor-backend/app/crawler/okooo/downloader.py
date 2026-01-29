# -*- coding: utf-8 -*-

import asyncio
import logging
import random
import os
from typing import Optional, Tuple, Any

from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)

class OkoooDownloader:
    """
    Okooo下载器
    负责页面HTML的下载，包含反爬处理和WAF检测
    """
    
    def __init__(self, headless: bool = True, is_mobile: bool = False, storage_state_path: Optional[str] = None, proxy_url: Optional[str] = None):
        self.headless = headless
        self.is_mobile = is_mobile
        self.storage_state_path = storage_state_path
        self.proxy_url = proxy_url
        self.playwright = None
        self.browser = None
        self.context = None
        self._lock = asyncio.Lock()
        
        # Simple proxy list (TODO: Move to config or DB)
        self.proxies = [proxy_url] if proxy_url else [
            # Example format: "http://user:pass@host:port"
            # None means direct connection
            None
        ]
        self.current_proxy_index = 0

    async def close(self):
        """关闭资源"""
        async with self._lock:
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
        if self.context and self.browser and self.playwright:
            return

        async with self._lock:
            # Double check after acquiring lock
            if self.context and self.browser and self.playwright:
                return

            if not self.playwright:
                self.playwright, self.browser, self.context = await self._create_browser_context()
            elif not self.browser:
                self.playwright, self.browser, self.context = await self._create_browser_context()
            elif not self.context:
                self.context = await self._create_context(self.browser)

    async def download(self, url: str) -> Optional[str]:
        """别名方法"""
        return await self.download_html(url)
    
    async def _rotate_proxy(self):
        """Rotate to next proxy"""
        if not self.proxies or len(self.proxies) <= 1:
            return
            
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        proxy = self.proxies[self.current_proxy_index]
        logger.info(f"Rotated to proxy index {self.current_proxy_index}: {proxy if proxy else 'Direct'}")

    async def _reset_context(self):
        """重置浏览器上下文（更换UA、指纹和代理）"""
        async with self._lock:
            if self.context:
                try:
                    await self.context.close()
                except Exception:
                    pass
                self.context = None
            
            # Rotate proxy before creating new context
            await self._rotate_proxy()
            
            if self.browser:
                self.context = await self._create_context(self.browser)
                # 重新注入反爬脚本
                await self.context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    window.chrome = {runtime: {}};
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: 'denied' }) :
                            originalQuery(parameters)
                    );
                """)
                logger.info("Browser context reset with new UA/fingerprint.")

    async def _check_captcha(self, page) -> bool:
        """
        检查是否存在滑块验证码
        """
        try:
            # Check for Aliyun captcha elements
            if await page.query_selector("#nc_1_n1z") or \
               await page.query_selector(".nc-container") or \
               await page.query_selector("div[id*='nc_'][class*='container']") or \
               await page.query_selector(".errloading > .slider"):
                return True
            
            content = await page.content()
            if "您的访问被阻断" in content or "滑动验证" in content or "请按住滑块" in content or "验证码" in content:
                # Double check to avoid false positives on pages that just mention "verification code" (like login inputs)
                # But for crawler, any mention usually means trouble
                if "请输入验证码" in content and "login" not in page.url:
                     return True
                if "滑动验证" in content or "您的访问被阻断" in content:
                     return True
                     
        except Exception as e:
            logger.error(f"Error checking captcha: {e}")
        return False

    async def _simulate_human_behavior(self, page):
        """模拟人类操作行为"""
        try:
            # 1. 随机移动鼠标 (更复杂的轨迹)
            for _ in range(random.randint(2, 4)):
                await page.mouse.move(
                    random.randint(100, 1000),
                    random.randint(100, 800),
                    steps=random.randint(10, 20)
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))

            # 2. 随机滚动 (模拟阅读)
            total_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            # 向下滚动
            scroll_amount = random.randint(300, 700)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # 偶尔向上回滚
            if random.random() < 0.3:
                await page.evaluate(f"window.scrollBy(0, -{random.randint(100, 300)})")
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 3. 再次移动鼠标
            await page.mouse.move(
                random.randint(100, 1000),
                random.randint(100, 800),
                steps=random.randint(5, 10)
            )
            
        except Exception:
            pass

    async def download_html(self, url: str, retries: int = 5) -> Optional[str]:
        """
        下载HTML内容，支持重试和自动过验证
        """
        last_error = None
        
        for attempt in range(retries):
            page = None
            try:
                await self._ensure_context()
                page = await self.context.new_page()
                
                try:
                    # 使用 strict load state 确保页面完全加载
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    
                    # 模拟人类行为
                    await self._simulate_human_behavior(page)
                    
                    # 额外等待以确保动态内容加载，并保持页面停留
                    # 增加等待时间以降低频率
                    await page.wait_for_timeout(random.randint(5000, 10000))
                    
                    # 检查验证码
                    if await self._check_captcha(page):
                        logger.warning(f"Detected captcha for {url} (Attempt {attempt+1}/{retries}). Resetting context...")
                        await page.close()
                        page = None
                        await self._reset_context()
                        continue

                    content = await page.content()
                    title = await page.title()
                    
                    # Check for blocking
                    if self._is_blocked(content, title, page.url, url):
                        logger.warning(f"Blocked or empty content for {url} (Attempt {attempt+1}/{retries})")
                        last_error = "Blocked or empty content"
                        # 如果是被拦截，也尝试重置上下文
                        await page.close()
                        page = None
                        await self._reset_context()
                        continue
                    
                    return content
                    
                except Exception as e:
                    logger.error(f"Page goto error for {url} (Attempt {attempt+1}/{retries}): {e}")
                    last_error = e
                    # 发生错误也尝试重置
                    if page:
                        await page.close()
                        page = None
                    await self._reset_context()
                    
            except Exception as e:
                logger.error(f"Download error for {url} (Attempt {attempt+1}/{retries}): {e}")
                last_error = e
                await self._reset_context()
                
            finally:
                if page:
                    try:
                        await page.close()
                    except:
                        pass
                
                # Retry delay
                if attempt < retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    
        logger.error(f"Failed to download {url} after {retries} attempts. Last error: {last_error}")
        return None

    def _get_random_ua(self, is_mobile: bool) -> str:
        """生成随机UA"""
        if is_mobile:
            ios_versions = ['16_0', '16_1', '16_2', '16_3', '17_0', '17_1', '17_2']
            v = random.choice(ios_versions)
            return f'Mozilla/5.0 (iPhone; CPU iPhone OS {v} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        else:
            mac_versions = ['10_15_7', '11_0_0', '12_0_0', '13_0_0', '14_0_0']
            chrome_versions = ['120.0.0.0', '121.0.0.0', '122.0.0.0', '123.0.0.0']
            m = random.choice(mac_versions)
            c = random.choice(chrome_versions)
            return f'Mozilla/5.0 (Macintosh; Intel Mac OS X {m}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{c} Safari/537.36'

    async def _create_context(self, browser: Browser) -> BrowserContext:
        """Create context with config"""
        # Randomize UA
        user_agent = self._get_random_ua(self.is_mobile)
        
        if self.is_mobile:
            viewport = {'width': 375, 'height': 812}
            is_mobile_device = True
            sec_ch_ua_platform = '"iOS"'
            sec_ch_ua_mobile = "?1"
        else:
            viewport = {'width': 1920, 'height': 1080}
            is_mobile_device = False
            sec_ch_ua_platform = '"macOS"'
            sec_ch_ua_mobile = "?0"
            
        # Randomize timezone slightly? No, stick to Shanghai but maybe randomize geolocation slightly
        lat = 31.2304 + random.uniform(-0.1, 0.1)
        lng = 121.4737 + random.uniform(-0.1, 0.1)
        
        # Proxy config
        proxy = self.proxies[self.current_proxy_index] if self.proxies else None
        proxy_config = {"server": proxy} if proxy else None

        context = await browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            is_mobile=is_mobile_device,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation'],
            geolocation={'latitude': lat, 'longitude': lng},
            color_scheme='light',
            ignore_https_errors=True,
            proxy=proxy_config,
            # Disable storage state loading to ensure fresh session
            # storage_state=self.storage_state_path if os.path.exists(self.storage_state_path or "") else None
        )
        
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
        try:
            context = await self._create_context(browser)
        except Exception:
            await browser.close()
            await p.stop()
            raise
        
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

    async def _check_and_wait_for_captcha(self, page) -> bool:
        """
        [已弃用] 检查是否存在滑块验证码，如果存在则等待用户手动处理
        现在使用 _check_captcha 和 _reset_context 替代
        """
        return await self._check_captcha(page)

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
