#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信API - 获取全部A股
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq

# 初始化TQ
tq.initialize(__file__)

print("=" * 60)
print("测试通达信API - 获取全部A股")
print("=" * 60)

# 1. 测试获取全部A股
print("\n1. 测试获取全部A股 (list_type=5):")
try:
    stocks = tq.get_stock_list(list_type=5)
    print(f"   获取到 {len(stocks)} 只A股")
    if stocks:
        print(f"   前10只股票: {stocks[:10]}")
        print(f"   类型: {type(stocks[0])}")
except Exception as e:
    print(f"   错误: {e}")

# 2. 测试获取市场数据（前10只）
print("\n2. 测试获取市场数据 (前10只):")
try:
    if stocks:
        test_stocks = stocks[:10]
        data = tq.get_market_data(
            field_list=['Close', 'Volume', 'Open', 'High', 'Low'],
            stock_list=test_stocks,
            period='1d',
            count=5,
            dividend_type='front',
            fill_data=True
        )
        print(f"   数据获取成功")
        print(f"   数据类型: {type(data)}")
        if isinstance(data, dict):
            print(f"   包含字段: {list(data.keys())}")
            if 'Close' in data:
                print(f"   收盘价数据形状: {data['Close'].shape}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
