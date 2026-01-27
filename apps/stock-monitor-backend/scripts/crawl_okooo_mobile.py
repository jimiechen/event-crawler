#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import random
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from playwright.async_api import async_playwright, Page, BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OkoooMobileCrawl")

class OkoooMobileCrawler:
    def __init__(self):
        self.base_url = "https://m.okooo.com"
        self.output_dir = os.path.join(os.getcwd(), "data", "okooo", "mobile")
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def create_context(self, p):
        """
        Create a browser context configured for mobile emulation with anti-detection
        """
        # Emulate iPhone 13
        iphone_13 = p.devices['iPhone 13']
        
        # Launch browser (Chromium is usually best for mobile emulation)
        # Added args to reduce detection surface
        args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
        
        browser = await p.chromium.launch(headless=True, args=args)
        
        context = await browser.new_context(
            **iphone_13,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation'],
            geolocation={'latitude': 31.2304, 'longitude': 121.4737}, # Shanghai
            color_scheme='light',
        )
        
        # Inject advanced anti-detection scripts
        await context.add_init_script("""
            // 1. Overwrite navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 2. Mock plugins (Mobile usually has 0, but let's be safe or empty)
            Object.defineProperty(navigator, 'plugins', {
                get: () => []
            });
            
            // 3. Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
            
            // 4. Mock WebGL vendor/renderer to look like real Apple GPU
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Apple Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Apple GPU';
                }
                return getParameter(parameter);
            };
            
            // 5. Mock Touch Events (ensure they exist)
            if (!('ontouchstart' in window)) {
                window.ontouchstart = null;
            }
        """)
        
        return context, browser

    async def human_behavior_simulation(self, page: Page):
        """
        Simulate human-like scrolling and interaction
        """
        # Random scroll
        total_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        
        current_scroll = 0
        while current_scroll < total_height:
            # Scroll amount: random between 1/3 and 2/3 of viewport
            scroll_amount = random.randint(int(viewport_height/3), int(viewport_height*2/3))
            current_scroll += scroll_amount
            
            # Use touch simulation if possible, or simple scroll
            await page.evaluate(f"window.scrollTo(0, {current_scroll})")
            
            # Random pause
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Occasional small scroll back (reading behavior)
            if random.random() < 0.3:
                await page.evaluate(f"window.scrollTo(0, {current_scroll - 100})")
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
            # Update total height in case of infinite scroll
            total_height = await page.evaluate("document.body.scrollHeight")
            
            # Don't scroll too far if page is huge
            if current_scroll > 3000: 
                break

    async def fetch_url(self, context: BrowserContext, url: str, name: str):
        """
        Fetch a single URL with WAF bypass logic
        """
        page = await context.new_page()
        
        try:
            logger.info(f"Processing: {name} -> {url}")
            
            # 1. Visit Homepage first to get cookies/session if not already set
            # Check if we already have cookies
            cookies = await context.cookies("https://m.okooo.com")
            has_acw = any(c['name'] == 'acw_tc' for c in cookies)
            
            if not has_acw:
                logger.info("Initializing session via homepage...")
                await page.goto("https://m.okooo.com/", wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))
            
            # 2. Navigate to target URL with Referer
            # Update Referer to look like internal navigation
            await page.set_extra_http_headers({
                "Referer": "https://m.okooo.com/jczq/",
            })
            
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # 3. Check for WAF
            if response.status == 405:
                logger.error(f"Blocked (405) for {name}")
                return False
                
            content = await page.content()
            title = await page.title()
            
            if "www.aliyun.com" in content or "您的访问被阻断" in content:
                logger.error(f"WAF Block Detected for {name}")
                return False
                
            # 4. Human Behavior
            logger.info(f"Loaded {name}. Simulating reading...")
            await self.human_behavior_simulation(page)
            
            # 5. Save Content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(await page.content())
                
            logger.info(f"Successfully saved {name} to {filepath}")
            
            # Optional: Take screenshot for verification
            screenshot_path = os.path.join(self.output_dir, f"{name}_{timestamp}.png")
            await page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
            return False
        finally:
            await page.close()

    async def run(self):
        async with async_playwright() as p:
            context, browser = await self.create_context(p)
            
            match_ids = [
                "1307926", "1302755", "1301405", "1315692", "1292778", "1301409", "1299479", "1299478",
                "1313606", "1296657", "1292782", "1299948", "1296658", "1307927", "1292780", "1301401",
                "1302751", "1302758", "1302752", "1307612", "1314249", "1292784", "1296659", "1299946",
                "1315660", "1295956", "1301404", "1292775", "1307933", "1307619", "1314245", "1292783",
                "1313605", "1301407", "1295955", "1295958", "1302753", "1320760", "1296654", "1295962"
            ]
            
            total_targets = len(match_ids) * 7
            processed_count = 0
            success_count = 0
            
            logger.info(f"Starting batch crawl for {len(match_ids)} matches (Total {total_targets} pages)")

            for match_id in match_ids:
                targets = [
                    {
                        "name": f"history_{match_id}",
                        "url": f"https://m.okooo.com/match/history.php?MatchID={match_id}&from=%2Fjczq%2F"
                    },
                    {
                        "name": f"handicap_{match_id}",
                        "url": f"https://m.okooo.com/match/handicap.php?MatchID={match_id}&from=%2Fjczq%2F"
                    },
                    {
                        "name": f"odds_{match_id}",
                        "url": f"https://m.okooo.com/match/odds.php?MatchID={match_id}&from=%2Fjczq%2F"
                    },
                    {
                        "name": f"form_{match_id}",
                        "url": f"https://m.okooo.com/match/form.php?MatchID={match_id}&from=%2Fjczq%2F"
                    },
                    {
                        "name": f"game_{match_id}",
                        "url": f"https://m.okooo.com/match/game.php?MatchID={match_id}&from=%2Fjczq%2F"
                    },
                    {
                        "name": f"game_recent_{match_id}",
                        "url": f"https://m.okooo.com/match/game.php?MatchID={match_id}&from=%2Fjczq%2F&type=recent"
                    },
                    {
                        "name": f"exchanges_{match_id}",
                        "url": f"https://m.okooo.com/match/exchanges.php?MatchID={match_id}&from=%2Fjczq%2F"
                    }
                ]
                
                for target in targets:
                    processed_count += 1
                    logger.info(f"[{processed_count}/{total_targets}] Processing {target['name']}")
                    
                    if await self.fetch_url(context, target['url'], target['name']):
                        success_count += 1
                    
                    # Random delay between requests
                    delay = random.uniform(5, 10)
                    logger.info(f"Sleeping for {delay:.2f}s...")
                    await asyncio.sleep(delay)
            
            logger.info(f"Batch Job complete. Success: {success_count}/{total_targets}")
            await browser.close()

if __name__ == "__main__":
    crawler = OkoooMobileCrawler()
    asyncio.run(crawler.run())
