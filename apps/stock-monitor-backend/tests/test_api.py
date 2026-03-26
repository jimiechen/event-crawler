#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API接口
"""

import asyncio
import requests

async def test_api():
    """测试API接口"""
    base_url = "http://localhost:8000"
    
    # 测试健康检查
    print("=" * 60)
    print("测试API接口")
    print("=" * 60)
    
    # 1. 测试健康检查
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"\n✅ 健康检查: {r.status_code}")
        print(f"   响应: {r.json()}")
    except Exception as e:
        print(f"\n❌ 健康检查失败: {e}")
    
    # 2. 测试问财批次列表（全部）
    try:
        r = requests.get(f"{base_url}/api/v1/wencai/batches?limit=5", timeout=10)
        print(f"\n✅ 批次列表(全部): {r.status_code}")
        data = r.json()
        print(f"   成功: {data.get('success')}")
        print(f"   数量: {len(data.get('data', []))}")
        if data.get('data'):
            print(f"   第一条: {data['data'][0]}")
    except Exception as e:
        print(f"\n❌ 批次列表(全部)失败: {e}")
    
    # 3. 测试问财批次列表（TDX来源）
    try:
        r = requests.get(f"{base_url}/api/v1/wencai/batches?source=tdx&limit=5", timeout=10)
        print(f"\n✅ 批次列表(TDX): {r.status_code}")
        data = r.json()
        print(f"   成功: {data.get('success')}")
        print(f"   数量: {len(data.get('data', []))}")
    except Exception as e:
        print(f"\n❌ 批次列表(TDX)失败: {e}")
    
    # 4. 测试问财批次列表（问财来源）
    try:
        r = requests.get(f"{base_url}/api/v1/wencai/batches?source=wencai&limit=5", timeout=10)
        print(f"\n✅ 批次列表(问财): {r.status_code}")
        data = r.json()
        print(f"   成功: {data.get('success')}")
        print(f"   数量: {len(data.get('data', []))}")
    except Exception as e:
        print(f"\n❌ 批次列表(问财)失败: {e}")
    
    # 5. 测试问财股票数据
    try:
        r = requests.get(f"{base_url}/api/v1/wencai/stocks?limit=5", timeout=10)
        print(f"\n✅ 股票数据: {r.status_code}")
        data = r.json()
        print(f"   成功: {data.get('success')}")
        print(f"   数量: {len(data.get('data', []))}")
    except Exception as e:
        print(f"\n❌ 股票数据失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_api())
