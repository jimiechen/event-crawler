#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找历史数据中出现3倍量的日期
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq
from datetime import date

# 初始化
tq.initialize(__file__)

# 获取更长时间段的数据
print("获取2025-02-01到2025-03-25的数据...")

data = tq.get_market_data(
    field_list=['Volume'],
    stock_list=['000001.SZ', '000002.SZ', '600000.SH', '600703.SH', '600519.SH', '002594.SZ'],
    period='1d',
    start_time='20250201',
    end_time='20250325',
    dividend_type='front'
)

if 'Volume' in data:
    volume_df = data['Volume']
    print(f"\n获取到 {len(volume_df)} 天的数据")
    print(f"日期范围: {volume_df.index[0]} 至 {volume_df.index[-1]}")
    
    print("\n\n查找3倍量股票:")
    found_any = False
    
    for i in range(1, len(volume_df)):
        date_str = str(volume_df.index[i])[:10]
        found_for_date = False
        
        for stock in volume_df.columns:
            prev_vol = volume_df.iloc[i-1][stock]
            today_vol = volume_df.iloc[i][stock]
            
            if prev_vol > 0:
                ratio = today_vol / prev_vol
                if ratio >= 3.0:
                    if not found_for_date:
                        print(f"\n{date_str}:")
                        found_for_date = True
                    print(f"  🔥 {stock}: 前日={prev_vol:,.0f}, 今日={today_vol:,.0f}, 量比={ratio:.2f}")
                    found_any = True
    
    if not found_any:
        print("\n未找到3倍量的股票")
        print("\n最大量比记录:")
        max_ratios = []
        for i in range(1, len(volume_df)):
            for stock in volume_df.columns:
                prev_vol = volume_df.iloc[i-1][stock]
                today_vol = volume_df.iloc[i][stock]
                if prev_vol > 0:
                    ratio = today_vol / prev_vol
                    max_ratios.append((ratio, str(volume_df.index[i])[:10], stock))
        
        max_ratios.sort(reverse=True)
        for ratio, date_str, stock in max_ratios[:10]:
            print(f"  {date_str} {stock}: {ratio:.2f}")

print("\n检查完成")
