#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试通达信数据格式
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq
import pandas as pd
from datetime import date

# 初始化
tq.initialize(__file__)

# 获取数据
print("获取市场数据...")
data = tq.get_market_data(
    field_list=['Volume'],
    stock_list=['000001.SZ', '000002.SZ', '600000.SH'],
    period='1d',
    count=2,
    dividend_type='front'
)

print(f"\n数据类型: {type(data)}")
print(f"\n数据内容:")
print(data)

print(f"\n\n如果是字典，查看键:")
if isinstance(data, dict):
    print(f"键: {list(data.keys())}")
    for key, value in data.items():
        print(f"\n{key}:")
        print(f"  类型: {type(value)}")
        print(f"  内容: {value}")
        if hasattr(value, 'shape'):
            print(f"  形状: {value.shape}")

print("\n\n尝试转换为DataFrame...")
try:
    if isinstance(data, dict):
        # 尝试不同的转换方式
        print("\n方式1: 直接转换")
        df1 = pd.DataFrame(data)
        print(f"成功: {df1.shape}")
        print(df1)
except Exception as e:
    print(f"失败: {e}")

print("\n\n尝试获取历史数据...")
try:
    hist_data = tq.get_market_data(
        field_list=['Close', 'Volume'],
        stock_list=['000001.SZ'],
        period='1d',
        count=5,
        start_time='20250201',
        end_time='20250210'
    )
    print(f"历史数据类型: {type(hist_data)}")
    print(f"历史数据: {hist_data}")
except Exception as e:
    print(f"获取历史数据失败: {e}")

print("\n调试完成")
