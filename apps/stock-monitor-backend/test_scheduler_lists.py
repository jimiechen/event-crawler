import asyncio
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from app.crawler.okooo.scheduler import OkoooScheduler
    from app.crawler.okooo.downloader import OkoooDownloader
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)

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
        class AsyncSession:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
        return AsyncSession()

async def main():
    db_manager = MockDBManager()
    redis_service = MockRedisService()
    
    scheduler = OkoooScheduler(db_manager=db_manager, redis_service=redis_service)
    
    # Use session file
    session_file = os.path.join(current_dir, "okooo_session_fix.json")
    
    print(f"Testing list fetch with session: {session_file}")
    
    await scheduler.configure(
        headless=False,  # Headed as requested
        is_mobile=True,
        storage_state_path=session_file
    )
    
    # Test fetch_match_lists
    print("Fetching match lists...")
    matches = await scheduler.fetch_match_lists()
    
    print(f"Found {len(matches)} matches.")
    if matches:
        print(f"First match: {matches[0]}")
        
    await scheduler.close()

if __name__ == "__main__":
    asyncio.run(main())
