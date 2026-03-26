#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看通达信API帮助
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq
import inspect

# 初始化TQ
tq.initialize(__file__)

print("=" * 60)
print("通达信API - get_stock_list 帮助信息")
print("=" * 60)

# 查看 get_stock_list 的签名
print("\n1. get_stock_list 函数签名:")
try:
    sig = inspect.signature(tq.get_stock_list)
    print(f"   {sig}")
    
    # 查看参数说明
    for name, param in sig.parameters.items():
        print(f"   - {name}: {param.default if param.default is not inspect.Parameter.empty else '必填'}")
except Exception as e:
    print(f"   错误: {e}")

# 查看 get_stock_list_in_sector 的签名
print("\n2. get_stock_list_in_sector 函数签名:")
try:
    sig = inspect.signature(tq.get_stock_list_in_sector)
    print(f"   {sig}")
except Exception as e:
    print(f"   错误: {e}")

# 查看 get_user_sector 的签名
print("\n3. get_user_sector 函数签名:")
try:
    sig = inspect.signature(tq.get_user_sector)
    print(f"   {sig}")
except Exception as e:
    print(f"   错误: {e}")

# 尝试不同方式调用 get_stock_list
print("\n4. 测试不同参数调用 get_stock_list:")

# 方式1: 无参数
try:
    stocks = tq.get_stock_list()
    print(f"   无参数: 获取到 {len(stocks)} 只股票")
except Exception as e:
    print(f"   无参数错误: {e}")

# 方式2: 带 market 参数
try:
    stocks = tq.get_stock_list(market='SH')
    print(f"   market='SH': 获取到 {len(stocks)} 只股票")
except Exception as e:
    print(f"   market='SH' 错误: {e}")

# 方式3: 带 type 参数（可能是type而不是list_type）
try:
    stocks = tq.get_stock_list(type=5)
    print(f"   type=5: 获取到 {len(stocks)} 只股票")
except Exception as e:
    print(f"   type=5 错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
