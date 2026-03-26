#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查特定日期的量比
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq
from datetime import date

# 初始化
tq.initialize(__file__)

# 获取2025-02-05到2025-02-07的数据
print("获取2025-02-05到2025-02-07的数据...")

data = tq.get_market_data(
    field_list=['Volume', 'Close'],
    stock_list=['000001.SZ', '600703.SH', '600519.SH'],
    period='1d',
    start_time='20250201',
    end_time='20250210',
    dividend_type='front'
)

if 'Volume' in data:
    volume_df = data['Volume']
    print("\n成交量数据:")
    print(volume_df)
    
    print("\n\n计算量比:")
    for i in range(1, len(volume_df)):
        date_str = str(volume_df.index[i])[:10]
        print(f"\n{date_str}:")
        for stock in volume_df.columns:
            prev_vol = volume_df.iloc[i-1][stock]
            today_vol = volume_df.iloc[i][stock]
            if prev_vol > 0:
                ratio = today_vol / prev_vol
                print(f"  {stock}: 前日={prev_vol:,.0f}, 今日={today_vol:,.0f}, 量比={ratio:.2f}")

if 'Close' in data:
    close_df = data['Close']
    print("\n\n收盘价数据:")
    print(close_df)

print("\n检查完成")
