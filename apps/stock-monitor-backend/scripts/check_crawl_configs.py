#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.okooo_service import OkoooService

async def check():
    service = OkoooService()
    scheduler = await service.get_scheduler()
    configs = await scheduler.get_db_crawl_configs()
    print(f'Found {len(configs)} crawl configs:')
    for c in configs[:5]:
        print(f'  - {c}')

if __name__ == "__main__":
    asyncio.run(check())
