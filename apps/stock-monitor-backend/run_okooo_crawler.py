#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import argparse
import sys
import os

# Add current directory to path so imports work
sys.path.append(os.getcwd())

from app.database import DatabaseManager
from app.services.redis_cache_service import RedisCacheService
from app.crawler.okooo.scheduler import OkoooScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='Okooo Crawler')
    parser.add_argument('--force', action='store_true', help='Force crawl even if duplicate')
    parser.add_argument('--headless', action='store_true', default=True, help='Use headless browser')
    parser.add_argument('--no-headless', dest='headless', action='store_false')
    args = parser.parse_args()

    # Initialize services
    db_manager = DatabaseManager()
    redis_service = RedisCacheService()
    
    # Initialize scheduler
    scheduler = OkoooScheduler(db_manager, redis_service)
    
    # Configure
    await scheduler.configure(headless=args.headless, is_mobile=True)
    
    # Target URLs
    urls = [
        "https://m.okooo.com/jczq/",
        "https://m.okooo.com/bjdc/"
    ]
    
    try:
        await scheduler.crawl_lists(urls, force=args.force)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if scheduler.downloader:
            await scheduler.downloader.close()
            
if __name__ == "__main__":
    asyncio.run(main())
