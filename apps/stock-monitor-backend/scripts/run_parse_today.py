#!/usr/bin/env python3
"""
直接运行今天的解析任务
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.okooo_parser_service import okooo_parser_service

async def main():
    print("🚀 开始解析 2026-02-02 的比赛数据...")
    result = await okooo_parser_service.parse_daily_matches("2026-02-02")
    print(f"\n📊 解析结果:")
    print(f"   日期: {result.get('date')}")
    print(f"   总数: {result.get('total')}")
    print(f"   成功: {result.get('processed')}")
    print(f"   失败: {result.get('failed')}")
    print(f"   输出目录: {result.get('output_dir')}")
    
    if result.get('failed_matches'):
        print(f"\n❌ 失败的比赛:")
        for item in result['failed_matches']:
            print(f"   - {item['match_id']}: {item['error']}")

if __name__ == "__main__":
    asyncio.run(main())
