#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信API
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq

# 初始化TQ
tq.initialize(__file__)

print("=" * 60)
print("测试通达信API")
print("=" * 60)

# 1. 测试获取板块列表
print("\n1. 测试获取用户自定义板块列表:")
try:
    sectors = tq.get_user_sector()
    print(f"   获取到 {len(sectors)} 个板块")
    if sectors:
        print(f"   前3个板块: {sectors[:3]}")
except Exception as e:
    print(f"   错误: {e}")

# 2. 测试获取通达信88板块股票
print("\n2. 测试获取 '通达信88' 板块股票:")
try:
    stocks = tq.get_stock_list_in_sector('通达信88')
    print(f"   获取到 {len(stocks)} 只股票")
    if stocks:
        print(f"   前5只股票: {stocks[:5]}")
        print(f"   类型: {type(stocks[0])}")
except Exception as e:
    print(f"   错误: {e}")

# 3. 测试获取市场数据
print("\n3. 测试获取市场数据 (前5只):")
try:
    if stocks:
        test_stocks = stocks[:5]
        data = tq.get_market_data(
            field_list=['Close', 'Volume'],
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
except Exception as e:
    print(f"   错误: {e}")

# 4. 测试获取股票详细信息
print("\n4. 测试获取股票详细信息:")
try:
    if stocks:
        test_stock = stocks[0]
        info = tq.get_more_info(test_stock)
        print(f"   股票 {test_stock} 信息:")
        print(f"   {info}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
