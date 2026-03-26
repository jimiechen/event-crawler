#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端API调用
模拟前端页面的请求
"""

import requests

base_url = "http://localhost:8000"

print("=" * 60)
print("测试前端API调用")
print("=" * 60)

# 1. 获取批次列表
print("\n1. 获取TDX批次列表:")
try:
    r = requests.get(f"{base_url}/api/v1/wencai/batches?source=tdx&limit=5")
    result = r.json()
    if result.get('success') and result.get('data'):
        batches = result['data']
        print(f"   找到 {len(batches)} 个TDX批次")
        
        # 获取第一个批次的ID
        if batches:
            first_batch = batches[0]
            batch_id = first_batch['id']
            print(f"   第一个批次ID: {batch_id}, 名称: {first_batch.get('batch_name')}")
            
            # 2. 获取该批次的股票数据
            print(f"\n2. 获取批次 {batch_id} 的股票数据:")
            r2 = requests.get(f"{base_url}/api/v1/wencai/batches/{batch_id}/stocks?limit=500")
            result2 = r2.json()
            
            print(f"   API状态: {r2.status_code}")
            print(f"   success: {result2.get('success')}")
            print(f"   message: {result2.get('message')}")
            print(f"   data类型: {type(result2.get('data'))}")
            
            if result2.get('data') and isinstance(result2.get('data'), list):
                records = result2['data']
                print(f"   股票数量: {len(records)}")
                
                if records:
                    print(f"\n   第一条股票数据:")
                    stock = records[0]
                    print(f"     代码: {stock.get('stock_code')}")
                    print(f"     名称: {stock.get('stock_name')}")
                    print(f"     价格: {stock.get('current_price')}")
                    print(f"     涨幅: {stock.get('change_percent')}")
                    print(f"     来源: {stock.get('source')}")
            else:
                print(f"   警告: data为空或不是数组")
                print(f"   完整响应: {result2}")
    else:
        print(f"   没有找到TDX批次")
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
