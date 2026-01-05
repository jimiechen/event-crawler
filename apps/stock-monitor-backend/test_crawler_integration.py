import sys
import os
import asyncio
from datetime import datetime

# Add module path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
crawler_module_path = os.path.join(project_root, "modules/module-playwright-crawler/src")
if crawler_module_path not in sys.path:
    sys.path.append(crawler_module_path)

print(f"Added path: {crawler_module_path}")

try:
    from playwright_crawler import LovartCrawler, TempmailCrawler, StitchCrawler, DeepseekCrawler
    print("Successfully imported crawlers")
except ImportError as e:
    print(f"Failed to import crawlers: {e}")
    sys.exit(1)

async def test_crawler(name, crawler_cls, html_content):
    print(f"\n--- Testing {name} ---")
    crawler = crawler_cls()
    
    # Test check_login_status_from_html
    print("Testing check_login_status_from_html...")
    login_status = crawler.check_login_status_from_html(html_content)
    print(f"Login Status: {login_status}")
    
    # Test parse_html
    print("Testing parse_html...")
    parsed = crawler.parse_html(html_content)
    print(f"Parsed Data: {parsed}")
    
    return login_status, parsed

async def main():
    # Mock HTML contents
    lovart_html = "<html><head><title>Lovart Art</title></head><body><div class='avatar'>User</div></body></html>"
    tempmail_html = "<html><head><title>Temp Mail</title></head><body><div id='current-mail'>test@tm.com</div></body></html>"
    stitch_html = "<html><head><title>Stitch</title></head><body><div class='user-profile'>Profile</div></body></html>"
    deepseek_html = "<html><head><title>DeepSeek</title></head><body><div class='user-menu'>Menu</div></body></html>"
    
    await test_crawler("Lovart", LovartCrawler, lovart_html)
    await test_crawler("Tempmail", TempmailCrawler, tempmail_html)
    await test_crawler("Stitch", StitchCrawler, stitch_html)
    await test_crawler("Deepseek", DeepseekCrawler, deepseek_html)

if __name__ == "__main__":
    asyncio.run(main())
