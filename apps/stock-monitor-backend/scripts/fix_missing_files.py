import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project path
current_dir = os.getcwd()
sys.path.append(current_dir)

try:
    from app.crawler.okooo.scheduler import OkoooScheduler
    from app.crawler.okooo.url_builder import OkoooPageType
    from app.crawler.okooo.downloader import OkoooDownloader
except ImportError as e:
    print(f"Import error: {e}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

# Mocks
class MockRedisClient:
    def exists(self, key):
        return 0
    def set(self, key, value, ex=None):
        pass

class MockRedisService:
    def __init__(self):
        self.client = MockRedisClient()

class MockDBManager:
    def get_session(self):
        # returns an async context manager
        class AsyncSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
        return AsyncSession()

async def warmup_session(session_path: str):
    print("Warming up session...")
    downloader = OkoooDownloader(
        headless=False,
        is_mobile=True,
        storage_state_path=session_path
    )
    # Visit homepage to get cookies
    await downloader.download("https://m.okooo.com/")
    await asyncio.sleep(3) # Wait for redirects/cookies
    # Visit a list page to ensure we look like a real user
    await downloader.download("https://m.okooo.com/jczq/")
    await asyncio.sleep(2)
    print("Session warmed up.")

async def main():
    # Initialize mocks
    db_manager = MockDBManager()
    redis_service = MockRedisService()
    
    session_file = os.path.join(current_dir, "okooo_session_fix.json")
    
    # Create empty session file if not exists
    if not os.path.exists(session_file):
        with open(session_file, 'w') as f:
            f.write('{"cookies":[],"origins":[]}')
    
    # Warm up session first
    await warmup_session(session_file)

    scheduler = OkoooScheduler(db_manager=db_manager, redis_service=redis_service)
    # Configure with headless=False to bypass WAF, and use delay to avoid fast block
    # Note: Okooo might be blocking due to missing cookies or specific headers.
    # The default scheduler sets mobile=True by default for some list methods but configure's default is mobile=True.
    # However, for crawl_ids, we need to ensure we are using mobile mode if we are hitting mobile URLs.
    await scheduler.configure(
        headless=False, 
        is_mobile=True,
        storage_state_path=session_file
    )
    
    # Increase delay
    scheduler.delay = 5.0
    
    # IDs from user request
    match_ids = ['1320145', '1314467', '1320144', '1312541']
    
    # Page types requested: odds and handicap
    page_types = [
        OkoooPageType.MOBILE_ODDS,
        OkoooPageType.MOBILE_HANDICAP
    ]
    
    print(f"Starting crawl for {len(match_ids)} matches: {match_ids}")
    print(f"Page types: {[pt.value for pt in page_types]}")
    
    await scheduler.crawl_ids(match_ids, page_types)
    
    print("Crawl finished.")
    
    # Verify files
    base_dir = os.path.join(current_dir, "data", "okooo", "batch_html")
    for mid in match_ids:
        match_dir = os.path.join(base_dir, mid)
        print(f"\nChecking directory: {match_dir}")
        if os.path.exists(match_dir):
            files = os.listdir(match_dir)
            print(f"Files found: {files}")
            has_odds = "odds.html" in files
            has_handicap = "handicap.html" in files
            print(f"  odds.html: {'Found' if has_odds else 'MISSING'}")
            print(f"  handicap.html: {'Found' if has_handicap else 'MISSING'}")
        else:
            print("  Directory not found!")

if __name__ == "__main__":
    asyncio.run(main())
