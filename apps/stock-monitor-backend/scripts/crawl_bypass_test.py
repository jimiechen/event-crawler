
import asyncio
import random
import os
import sys
from playwright.async_api import async_playwright

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger

async def test_bypass():
    match_id = "1307926"  # Sample ID
    url = f"https://www.okooo.com/soccer/match/{match_id}/"
    home_url = "https://www.okooo.com/"
    
    logger.info(f"Starting WAF bypass test for match {match_id}")
    
    async with async_playwright() as p:
        # Launch options
        browser = await p.chromium.launch(
            headless=True,  # Set to False to debug visually if needed (but server env usually headless)
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation'],
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Stealth script
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {},
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        page = await context.new_page()
        
        try:
            # Step 1: Visit Homepage first to get cookies
            logger.info("Visiting homepage...")
            await page.goto(home_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(random.uniform(3, 5))
            
            # Step 2: Visit Match Page
            logger.info(f"Visiting match page: {url}")
            # Add Referer
            await page.set_extra_http_headers({
                "Referer": home_url
            })
            
            response = await page.goto(url, wait_until='commit', timeout=30000)
            logger.info(f"Response status: {response.status}")
            
            # Wait for content
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(random.uniform(5, 8))
            
            content = await page.content()
            logger.info(f"Content length: {len(content)}")
            
            if len(content) < 1000:
                logger.error("Content too short, likely blocked.")
                # Save screenshot for debug
                await page.screenshot(path="debug_block.png")
            else:
                logger.success("Content retrieved successfully!")
                # Save to file
                os.makedirs("data/okooo/raw_html/test", exist_ok=True)
                with open(f"data/okooo/raw_html/test/{match_id}.html", "w", encoding="utf-8") as f:
                    f.write(content)
                    
        except Exception as e:
            logger.error(f"Error during crawl: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_bypass())
