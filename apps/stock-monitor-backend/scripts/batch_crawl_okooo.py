#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
import random
import time
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler.okooo_crawler import OkoooCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BatchCrawl")

class MockOkoooCrawler(OkoooCrawler):
    def __init__(self):
        # Pass None as db since we mock methods that use it
        super().__init__(None)
        
    async def get_platform_config(self) -> Optional[Dict[str, Any]]:
        return {
            "domain": "okooo.com",
            "base_url": "https://www.okooo.com"
        }
        
    async def get_best_session(self) -> Optional[Dict[str, Any]]:
        return None
        
    async def create_browser_context(self):
        # Need to override this because base implementation calls get_platform_config from service
        # and also tries to use session service.
        # We'll use a simplified version for this script.
        
        from playwright.async_api import async_playwright
        
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
        browser = await p.chromium.launch(headless=True, args=args)
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation'],
            geolocation={'latitude': 31.2304, 'longitude': 121.4737}, # Shanghai
            color_scheme='light'
        )
        
        # Add comprehensive anti-detection scripts
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
        
        return context, None, browser

    async def fetch_page_source(self, query: str = None, debug_url: str = None) -> Optional[str]:
        # Override to provide better stability and logging
        context = None
        browser = None
        try:
            context, session, browser = await self.create_browser_context()
            
            # Randomize User Agent slightly
            chrome_version = random.randint(115, 120)
            ua = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
            
            # Enhanced Headers
            await context.set_extra_http_headers({
                "User-Agent": ua,
                "Referer": "https://www.okooo.com/",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Sec-Ch-Ua": f'"Not_A Brand";v="8", "Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            })
            
            page = await context.new_page()
            
            # Strategy: Visit Homepage First to establish session/cookies
            try:
                # logger.info("Visiting homepage to establish session...")
                await page.goto("https://www.okooo.com/", wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(random.uniform(2, 4))
                
                # Simulate some human interaction on homepage
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await page.evaluate("window.scrollTo(0, 200)")
                await asyncio.sleep(random.uniform(1, 2))
                
                # Simulate clicking a random link (optional, maybe too risky if it navigates away)
                # Instead, just hover
                await page.mouse.move(random.randint(200, 800), random.randint(200, 600))
                
            except Exception as e:
                logger.warning(f"Homepage visit failed: {e}, continuing...")

            target_url = debug_url if debug_url else self.base_url
            logger.info(f"Navigating to {target_url}")
            
            # Update Referer to homepage
            await page.set_extra_http_headers({
                "Referer": "https://www.okooo.com/",
            })

            # Use 'domcontentloaded' and then wait
            try:
                response = await page.goto(target_url, wait_until='domcontentloaded', timeout=40000)
                
                # Check response status
                if response and response.status == 405:
                    logger.error("Got 405 status code directly.")
                    return None
                    
            except Exception as e:
                logger.warning(f"Navigation warning: {e}, but continuing to check content...")

            await asyncio.sleep(random.uniform(4, 7)) # Give it some time for dynamic content
            
            # Simulate scrolling on target page
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/1.5)")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            content = await page.content()
            title = await page.title()
            logger.info(f"Page content length: {len(content)}, Title: {title}")
            
            # Check for specific WAF indicators
            if "www.aliyun.com" in content or "405" in title or "您的访问被阻断" in content:
                logger.error("Detected WAF Block (Aliyun 405).")
                return None
            
            # Check for redirect to homepage (soft block)
            if page.url == "https://www.okooo.com/" and target_url != "https://www.okooo.com/":
                 logger.error("Redirected to homepage (Soft Block).")
                 return None

            if len(content) < 1000:
                logger.warning("Content too short, possibly blocked or empty.")
                # Don't return short content as it might be an error page
                return None
            
            return content
            
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return None
        finally:
            if context: await context.close()
            if browser: await browser.close()


async def main():
    match_ids = [
        "1307926", "1302755", "1301405", "1315692", "1292778", "1301409", "1299479", "1299478",
        "1313606", "1296657", "1292782", "1299948", "1296658", "1307927", "1292780", "1301401",
        "1302751", "1302758", "1302752", "1307612", "1314249", "1292784", "1296659", "1299946",
        "1315660", "1295956", "1301404", "1292775", "1307933", "1307619", "1314245", "1292783",
        "1313605", "1301407", "1295955", "1295958", "1302753", "1320760", "1296654", "1295962"
    ]
    
    logger.info(f"Starting batch crawl for {len(match_ids)} matches")
    
    crawler = MockOkoooCrawler()
    
    # Batch name
    batch_name = f"OkoooBatch_{int(time.time())}"
    
    success_count = 0
    fail_count = 0
    
    for i, match_id in enumerate(match_ids):
        # Use direct URL to avoid redirects which might trigger WAF
        url = f"https://www.okooo.com/soccer/match/{match_id}/"
        logger.info(f"[{i+1}/{len(match_ids)}] Processing match {match_id}: {url}")
        
        try:
            # Use debug_url to force specific URL
            result = await crawler.fetch_and_parse(debug_url=url, batch_name=batch_name)
            
            if result and result.get("status") == "success":
                logger.info(f"Success: Saved to {result.get('raw_html_path')}")
                success_count += 1
            else:
                logger.error(f"Failed: {result}")
                fail_count += 1
                
        except Exception as e:
            logger.error(f"Exception processing {match_id}: {e}")
            fail_count += 1
            
        # Random delay 2-5 seconds
        delay = random.uniform(2, 5)
        logger.info(f"Sleeping for {delay:.2f}s...")
        await asyncio.sleep(delay)
        
    logger.info(f"Batch complete. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    asyncio.run(main())
