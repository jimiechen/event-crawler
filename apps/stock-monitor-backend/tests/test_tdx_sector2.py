#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信板块创建 - 检查股票代码格式
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq

# 初始化TQ
tq.initialize(__file__)

print("=" * 60)
print("测试通达信板块创建 - 股票代码格式")
print("=" * 60)

# 测试不同的股票代码格式
sector_code = "3BL260325"

# 格式1: 标准格式 (000001.SZ)
print("\n1. 测试标准格式 (000001.SZ):")
try:
    stocks1 = ["000001.SZ", "000002.SZ"]
    result = tq.send_user_block(block_code=sector_code, stocks=stocks1)
    print(f"   结果: {result}")
    stocks = tq.get_stock_list_in_sector(sector_code)
    print(f"   板块股票: {stocks}")
except Exception as e:
    print(f"   错误: {e}")

# 格式2: 无后缀格式 (000001)
print("\n2. 测试无后缀格式 (000001):")
try:
    stocks2 = ["000001", "000002"]
    result = tq.send_user_block(block_code=sector_code, stocks=stocks2)
    print(f"   结果: {result}")
    stocks = tq.get_stock_list_in_sector(sector_code)
    print(f"   板块股票: {stocks}")
except Exception as e:
    print(f"   错误: {e}")

# 格式3: 通达信格式 (000001.XSHE)
print("\n3. 测试通达信格式 (000001.XSHE):")
try:
    stocks3 = ["000001.XSHE", "000002.XSHE"]
    result = tq.send_user_block(block_code=sector_code, stocks=stocks3)
    print(f"   结果: {result}")
    stocks = tq.get_stock_list_in_sector(sector_code)
    print(f"   板块股票: {stocks}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
