#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.okooo_service import OkoooService

async def test():
    service = OkoooService()
    
    # 测试直接调用 repair_daily_data
    print("Testing repair_daily_data...")
    result = await service.repair_daily_data("2026-02-03", dry_run=False)
    print(f"Result: {result}")
    
    # 检查内存中的任务
    if hasattr(service, 'repair_tasks') and service.repair_tasks:
        print(f"\nMemory tasks: {len(service.repair_tasks)}")
    else:
        print("\nNo tasks in memory")
    
    # 检查Redis中的任务
    tasks = await service.get_repair_tasks()
    print(f"Redis tasks: {len(tasks)}")

if __name__ == "__main__":
    asyncio.run(test())
