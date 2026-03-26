#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间戳功能的脚本
验证Chrome扩展发送的时间戳数据能够正确处理和去重
"""

import asyncio
import json
import aiohttp
from datetime import datetime

async def test_single_request(session, data, test_name):
    """测试单个请求"""
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/stocks/tonghuashun/raw-data"
    
    print(f"\n📤 {test_name}...")
    try:
        async with session.post(f"{base_url}{endpoint}", json=data) as response:
            result = await response.json()
            print(f"✅ 响应状态: {response.status}")
            print(f"📊 响应结果: {result}")
            return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

async def test_timestamp_functionality():
    """测试时间戳功能"""
    
    # 测试数据
    test_data_1 = {
        "source": "thspanel",
        "data": [
            {
                "urlTimestamp": "1729987200000",  # 时间戳1
                "hs": [
                    ["000001", "平安银行", "12.50", "0.10", "0.81", "1000000", "12500000", "12.60", "12.40", "12.45"]
                ]
            }
        ]
    }
    
    test_data_2 = {
        "source": "thspanel", 
        "data": [
            {
                "urlTimestamp": "1729987200000",  # 相同时间戳（应该被去重）
                "hs": [
                    ["000001", "平安银行", "12.51", "0.11", "0.89", "1100000", "13750000", "12.61", "12.41", "12.46"]
                ]
            }
        ]
    }
    
    test_data_3 = {
        "source": "thspanel",
        "data": [
            {
                "urlTimestamp": "1729987260000",  # 不同时间戳（应该成功）
                "hs": [
                    ["000001", "平安银行", "12.52", "0.12", "0.97", "1200000", "15024000", "12.62", "12.42", "12.47"]
                ]
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        print("🚀 开始测试时间戳功能...")
        
        # 测试1: 发送第一个时间戳的数据
        await test_single_request(session, test_data_1, "测试1: 发送第一个时间戳的数据")
        
        # 等待一下
        await asyncio.sleep(1)
        
        # 测试2: 发送相同时间戳的数据（应该被去重）
        await test_single_request(session, test_data_2, "测试2: 发送相同时间戳的数据（应该被去重）")
        
        # 等待一下
        await asyncio.sleep(1)
        
        # 测试3: 发送不同时间戳的数据（应该成功）
        await test_single_request(session, test_data_3, "测试3: 发送不同时间戳的数据（应该成功）")

async def test_database_data():
    """测试数据库中的数据"""
    import aiomysql
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("\n🔍 检查数据库中的数据...")
    
    connection = await aiomysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'stock_user'),
        password=os.getenv('DB_PASSWORD', 'stock123456'),
        db=os.getenv('DB_DATABASE', 'stock_monitor'),
        charset='utf8mb4'
    )
    
    try:
        cursor = await connection.cursor()
        
        # 查询包含request_timestamp的数据
        await cursor.execute("""
            SELECT symbol, request_timestamp, close_price, created_at 
            FROM stock_prices 
            WHERE request_timestamp IS NOT NULL 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        rows = await cursor.fetchall()
        print(f"📊 数据库中包含时间戳的记录数: {len(rows)}")
        
        for row in rows:
            print(f"  股票: {row[0]}, 时间戳: {row[1]}, 价格: {row[2]}, 创建时间: {row[3]}")
        
    finally:
        await cursor.close()
        connection.close()

if __name__ == "__main__":
    print("🎯 开始测试时间戳功能...")
    
    # 运行API测试
    asyncio.run(test_timestamp_functionality())
    
    # 检查数据库数据
    asyncio.run(test_database_data())
    
    print("\n🎉 测试完成！")