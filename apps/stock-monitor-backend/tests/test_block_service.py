#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信板块服务
"""

from datetime import date
from app.services.tdx_block_service import TdxBlockService

print("=" * 60)
print("测试通达信板块服务")
print("=" * 60)

# 创建服务
service = TdxBlockService()

# 测试股票代码转换
print("\n1. 测试股票代码转换:")
test_codes = ["000001.SZ", "000002.SZ", "600000.SH", "600001.SH", "830899.BJ"]
for code in test_codes:
    converted = service._convert_stock_code(code)
    print(f"   {code} -> {converted}")

# 测试创建板块并写入股票
print("\n2. 测试创建板块并写入股票:")
trade_date = date(2026, 3, 25)
test_stocks = ["000001.SZ", "000002.SZ", "600000.SH", "600001.SH"]
try:
    block_code = service.create_block_and_write_stocks(trade_date, test_stocks)
    print(f"   创建板块: {block_code}")
    
    # 读取板块中的股票
    stocks = service.read_stocks_from_block(block_code)
    print(f"   板块中的股票: {stocks}")
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
