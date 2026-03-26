#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查通达信板块
"""

import sys
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from tqcenter import tq

# 初始化TQ
tq.initialize(__file__)

print("=" * 60)
print("检查通达信用户自定义板块")
print("=" * 60)

# 获取用户自定义板块列表
print("\n1. 用户自定义板块列表:")
try:
    sectors = tq.get_user_sector()
    print(f"   共 {len(sectors)} 个板块")
    
    # 查找3BL开头的板块
    bl_sectors = [s for s in sectors if s.get('Code', '').startswith('3BL')]
    print(f"\n   3BL开头的板块: {len(bl_sectors)} 个")
    for sector in bl_sectors:
        code = sector.get('Code', '')
        name = sector.get('Name', '')
        print(f"     - {code}: {name}")
        
        # 获取板块中的股票
        try:
            stocks = tq.get_stock_list_in_sector(code)
            print(f"       股票数: {len(stocks)}")
        except Exception as e:
            print(f"       获取股票失败: {e}")
            
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
