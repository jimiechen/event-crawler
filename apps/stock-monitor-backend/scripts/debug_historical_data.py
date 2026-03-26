#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试通达信历史数据获取
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq
from datetime import date

# 初始化
tq.initialize(__file__)

# 尝试获取历史数据
print("尝试获取历史数据...")

# 方式1: 使用start_time和end_time
try:
    data = tq.get_market_data(
        field_list=['Volume', 'Close'],
        stock_list=['000001.SZ', '600703.SH'],
        period='1d',
        start_time='20250201',
        end_time='20250210',
        dividend_type='front'
    )
    print(f"\n方式1成功，数据类型: {type(data)}")
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"{key}: {type(value)}")
            if hasattr(value, 'shape'):
                print(f"  形状: {value.shape}")
                print(f"  索引: {value.index.tolist()}")
                print(value)
except Exception as e:
    print(f"方式1失败: {e}")

# 方式2: 使用count
try:
    data = tq.get_market_data(
        field_list=['Volume'],
        stock_list=['000001.SZ'],
        period='1d',
        count=10,
        dividend_type='front'
    )
    print(f"\n方式2成功，数据类型: {type(data)}")
    if isinstance(data, dict) and 'Volume' in data:
        df = data['Volume']
        print(f"数据形状: {df.shape}")
        print(f"数据日期: {df.index.tolist()}")
        print(df)
except Exception as e:
    print(f"方式2失败: {e}")

print("\n调试完成")
