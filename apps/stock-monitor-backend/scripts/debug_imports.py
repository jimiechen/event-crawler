
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir) # apps/stock-monitor-backend
sys.path.append(backend_root)

print("Start imports")
try:
    print("Importing app.database...")
    from app.database import DatabaseManager
    print("app.database imported")

    print("Importing app.services.cookie_service...")
    from app.services.cookie_service import CookieService
    print("app.services.cookie_service imported")

    print("Importing app.services.wencai_service...")
    from app.services.wencai_service import WencaiService
    print("app.services.wencai_service imported")

    print("Importing playwright.async_api...")
    from playwright.async_api import async_playwright
    print("playwright.async_api imported")
    
    print("Importing app.crawler.wencai_crawler...")
    from app.crawler.wencai_crawler import WencaiCrawler
    print("app.crawler.wencai_crawler imported")
    
except Exception as e:
    print(f"Error: {e}")
