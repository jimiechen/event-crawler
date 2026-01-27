#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import random
import os
import sys
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from playwright.async_api import async_playwright, Page, BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SampleFetch")

class SampleFetcher:
    def __init__(self):
        self.base_url = "https://m.okooo.com"
        # Use absolute path for data directory
        self.output_dir = "/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/mobile_samples"
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def create_context(self, p):
        # Emulate iPhone 13
        iphone_13 = p.devices['iPhone 13']
        
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
            geolocation={'latitude': 31.2304, 'longitude': 121.4737},
            color_scheme='light',
        )
        
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Apple Inc.';
                if (parameter === 37446) return 'Apple GPU';
                return getParameter(parameter);
            };
            if (!('ontouchstart' in window)) { window.ontouchstart = null; }
        """)
        
        return context, browser

    async def fetch_url(self, context: BrowserContext, url: str, name: str):
        page = await context.new_page()
        try:
            logger.info(f"Processing: {name} -> {url}")
            
            cookies = await context.cookies("https://m.okooo.com")
            has_acw = any(c['name'] == 'acw_tc' for c in cookies)
            
            if not has_acw:
                logger.info("Initializing session via homepage...")
                await page.goto("https://m.okooo.com/", wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))
            
            await page.set_extra_http_headers({"Referer": "https://m.okooo.com/jczq/"})
            
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            if response.status == 405:
                logger.error(f"Blocked (405) for {name}")
                return False
                
            content = await page.content()
            if "www.aliyun.com" in content or "您的访问被阻断" in content:
                logger.error(f"WAF Block Detected for {name}")
                return False
                
            logger.info(f"Loaded {name}. Saving...")
            
            filename = f"{name}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(await page.content())
                
            logger.info(f"Successfully saved {name} to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
            return False
        finally:
            await page.close()

    async def main(self):
        async with async_playwright() as p:
            context, browser = await self.create_context(p)
            
            # Additional sample page for odds change
            urls = {
                "form_1314249": "https://m.okooo.com/match/form.php?MatchID=1314249&from=%2Fjczq%2F",
                "game_1314249": "https://m.okooo.com/match/game.php?MatchID=1314249&from=%2Fjczq%2F",
                "exchanges_1314249": "https://m.okooo.com/match/exchanges.php?MatchID=1314249&from=%2Fjczq%2F",
                "odds_change_1314249_82": "https://m.okooo.com/match/change.php?mid=1314249&pid=82&Type=Odds&c=6"
            }
            
            for name, url in urls.items():
                await self.fetch_url(context, url, name)
                # Random delay between requests
                await asyncio.sleep(random.uniform(2, 5))
                
            await browser.close()

if __name__ == "__main__":
    fetcher = SampleFetcher()
    asyncio.run(fetcher.main())
