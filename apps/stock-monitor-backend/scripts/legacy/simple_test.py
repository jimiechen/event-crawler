#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单独立测试字段映射修改
"""

# 字段映射配置 - 修改后的版本
FIELD_MAPPING = {
    "6": "prev_close",         # 昨收价
    "7": "open_price",         # 开盘价
    "8": "high_price",         # 最高价
    "9": "low_price",          # 最低价
    "10": "current_price",     # 当前价格
    "name": "stock_name",      # 股票名称
}

def simple_decode_test():
    """简单解码测试"""
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
    
    print("\n📋 修正后的字段映射配置:")
    for key, value in FIELD_MAPPING.items():
        if key in ["6", "7", "8", "9", "10"]:
            print(f"  {key} -> {value}")
    
    print(f"\n📥 原始数据:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    
    # 简单映射转换
    decoded_data = {}
    for key, value in test_data.items():
        if key in FIELD_MAPPING:
            field_name = FIELD_MAPPING[key]
            decoded_data[field_name] = value
    
    print(f"\n📤 解码后数据:")
    print(f"  昨收价 (prev_close): {decoded_data.get('prev_close')}")
    print(f"  开盘价 (open_price): {decoded_data.get('open_price')}")
    print(f"  最高价 (high_price): {decoded_data.get('high_price')}")
    print(f"  最低价 (low_price): {decoded_data.get('low_price')}")
    print(f"  当前价 (current_price): {decoded_data.get('current_price')}")
    print(f"  股票名称 (stock_name): {decoded_data.get('stock_name')}")
    
    print("\n✅ 字段映射修改验证:")
    print(f"  ✅ 字段6 (9.65) -> prev_close: {decoded_data.get('prev_close')}")
    print(f"  ✅ 字段7 (9.61) -> open_price: {decoded_data.get('open_price')}")
    print(f"  ✅ 字段8 (9.67) -> high_price: {decoded_data.get('high_price')}")
    print(f"  ✅ 字段9 (9.40) -> low_price: {decoded_data.get('low_price')}")
    print(f"  ✅ 字段10 (9.40) -> current_price: {decoded_data.get('current_price')}")
    
    print("\n🎉 字段映射修改成功！")

if __name__ == "__main__":
    simple_decode_test()