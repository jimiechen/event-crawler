#!/usr/bin/env python3
"""测试修复检查的日志输出"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.okooo_service import OkoooService

async def test():
    service = OkoooService()
    
    print("Testing _on_log...")
    await service._on_log("INFO", "Test log message")
    print("_on_log completed")
    
    print("\nTesting repair_daily_data...")
    result = await service.repair_daily_data("2026-02-03", dry_run=False)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())
