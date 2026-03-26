#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TDX数据同步
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 添加通达信路径
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import asyncio
from datetime import date

from app.services.tdx_data_sync_service import TdxDataSyncService


async def main():
    print("\n" + "="*60)
    print("TDX数据同步测试")
    print("="*60 + "\n")
    
    service = TdxDataSyncService()
    
    # 1. 测试通达信连接
    print("1. 测试通达信连接...")
    if service.initialize_tdx():
        print("   OK: 通达信连接成功\n")
    else:
        print("   FAIL: 通达信连接失败\n")
        return
    
    # 2. 测试获取数据
    print("2. 测试获取数据...")
    stock_codes = ['000001.SZ', '600000.SH', '000002.SZ']
    data = service._fetch_daily_data_from_tdx(stock_codes, date(2026, 3, 25), days=2)
    print(f"   获取到 {len(data)} 条数据\n")
    
    if data:
        print("   示例数据:")
        for d in data[:3]:
            print(f"   - {d['code']}: close={d['close']}, vol={d['vol']}")
        print()
    
    print("="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
