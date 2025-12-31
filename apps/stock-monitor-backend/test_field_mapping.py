#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试字段映射修改
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# 直接导入解码器类，避免其他依赖
from app.services.tonghuashun_data_decoder import TonghuashunDataDecoder

def test_field_mapping():
    """测试字段映射修改"""
    print("🧪 测试字段映射修改...")
    
    # 测试数据
    test_data = {
        "6": "9.65",   # 应该映射到 prev_close
        "7": "9.61",   # 应该映射到 open_price  
        "8": "9.67",   # 应该映射到 high_price
        "9": "9.40",   # 应该映射到 low_price
        "10": "9.40",  # 应该映射到 current_price
        "name": "赛摩智能"
    }
    
    decoder = TonghuashunDataDecoder()
    
    print("\n📋 字段映射配置:")
    for key, value in decoder.FIELD_MAPPING.items():
        if key in ["6", "7", "8", "9", "10"]:
            print(f"  {key} -> {value}")
    
    print(f"\n📥 原始数据:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    
    # 解码单个股票数据
    decoded_data = decoder.decode_stock_data(test_data)
    
    print(f"\n📤 解码后数据:")
    if decoded_data['success']:
        stock_data = decoded_data['data']
        print(f"  昨收价 (prev_close): {stock_data.get('prev_close')}")
        print(f"  开盘价 (open_price): {stock_data.get('open_price')}")
        print(f"  最高价 (high_price): {stock_data.get('high_price')}")
        print(f"  最低价 (low_price): {stock_data.get('low_price')}")
        print(f"  当前价 (current_price): {stock_data.get('current_price')}")
        print(f"  股票名称 (stock_name): {stock_data.get('stock_name')}")
    else:
        print(f"  解码失败: {decoded_data['message']}")
    
    print("\n✅ 字段映射修改验证完成!")

if __name__ == "__main__":
    test_field_mapping()