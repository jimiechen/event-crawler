#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信获取股票名称
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq
import json

# 初始化
tq.initialize(__file__)

# 测试获取股票名称
test_codes = ['000001.SZ', '600000.SH', '300001.SZ']

for code in test_codes:
    print(f"\n测试股票: {code}")
    try:
        info = tq.get_more_info(code)
        print(f"返回类型: {type(info)}")
        print(f"返回内容: {info}")
        
        if info:
            if isinstance(info, list) and len(info) > 0:
                print(f"第一条记录: {info[0]}")
                print(f"名称字段: {info[0].get('Name', 'N/A')}")
            elif isinstance(info, dict):
                print(f"字典类型: {info}")
                print(f"名称字段: {info.get('Name', 'N/A')}")
    except Exception as e:
        print(f"错误: {e}")

# 尝试其他方法获取名称
print("\n\n尝试 get_stock_info:")
try:
    info = tq.get_stock_info('000001.SZ')
    print(f"返回: {info}")
except Exception as e:
    print(f"错误: {e}")
