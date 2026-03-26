#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信板块创建
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq

# 初始化TQ
tq.initialize(__file__)

print("=" * 60)
print("测试通达信板块创建")
print("=" * 60)

# 1. 测试创建板块
print("\n1. 测试创建板块:")
sector_code = "3BL260325"
sector_name = "3倍量涨停260325"
try:
    result = tq.create_sector(block_code=sector_code, block_name=sector_name)
    print(f"   创建板块结果: {result}")
except Exception as e:
    print(f"   创建板块错误: {e}")

# 2. 测试写入股票到板块
print("\n2. 测试写入股票到板块:")
test_stocks = ["000001.SZ", "000002.SZ", "600000.SH"]
try:
    result = tq.send_user_block(block_code=sector_code, stocks=test_stocks)
    print(f"   写入股票结果: {result}")
except Exception as e:
    print(f"   写入股票错误: {e}")

# 3. 测试获取板块中的股票
print("\n3. 测试获取板块中的股票:")
try:
    stocks = tq.get_stock_list_in_sector(sector_code)
    print(f"   板块 {sector_code} 中的股票: {stocks}")
except Exception as e:
    print(f"   获取板块股票错误: {e}")

# 4. 测试获取用户自定义板块列表
print("\n4. 测试获取用户自定义板块列表:")
try:
    sectors = tq.get_user_sector()
    print(f"   用户板块数量: {len(sectors)}")
    # 查找我们创建的板块
    for sector in sectors:
        if sector.get('Code') == sector_code:
            print(f"   找到板块: {sector}")
except Exception as e:
    print(f"   获取板块列表错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
