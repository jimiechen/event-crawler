#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API集成测试脚本
测试所有API端点的功能和响应
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from httpx import AsyncClient
from app.main import app

class DecimalEncoder(json.JSONEncoder):
    """处理Decimal类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def test_health_check():
    """测试健康检查端点"""
    print("🔍 测试健康检查端点...")
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    print("✅ 健康检查测试通过\n")

async def test_stock_crud():
    """测试股票CRUD操作"""
    print("🔍 测试股票CRUD操作...")
    
    # 创建股票信息
    stock_data = {
        "code": "000001",
        "name": "平安银行",
        "market": "SZ",
        "industry": "银行",
        "is_active": True
    }
    
    response = await client.post("/api/v1/stocks/info", json=stock_data)
    assert response.status_code == 200, f"创建股票失败: {response.status_code} - {response.text}"
    
    # 获取股票信息
    response = await client.get("/api/v1/stocks/info/000001")
    assert response.status_code == 200, f"获取股票失败: {response.status_code} - {response.text}"
    
    # 更新股票信息
    update_data = {"name": "平安银行(更新)"}
    response = await client.put("/api/v1/stocks/info/000001", json=update_data)
    assert response.status_code == 200, f"更新股票失败: {response.status_code} - {response.text}"
    
    # 获取股票列表
    response = await client.get("/api/v1/stocks/info")
    assert response.status_code == 200, f"获取股票列表失败: {response.status_code} - {response.text}"
    
    print("✅ 股票CRUD操作测试通过")

async def test_stock_data_crud():
    """测试股票数据CRUD操作"""
    print("🔍 测试股票数据CRUD操作...")
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # 先创建股票信息
        stock_info = {
            "code": "000002",
            "name": "万科A",
            "market": "sz"
        }
        await client.post("/api/stocks/", json=stock_info)
        
        # 测试创建股票数据
        stock_data = {
            "code": "000002",
            "name": "万科A",
            "price": 25.50,
            "change_amount": 0.50,
            "change_percent": 2.00,
            "volume": 1000000,
            "turnover": 25500000.0,
            "high": 26.00,
            "low": 25.00,
            "open_price": 25.20,
            "prev_close": 25.00,
            "timestamp": datetime.now().isoformat()
        }
        response = await client.post("/api/stock-data/", json=stock_data)
        print(f"创建股票数据 - 状态码: {response.status_code}")
        if response.status_code == 201:
            created_data = response.json()
            print(f"创建成功: {created_data['code']} - 价格: {created_data['price']}")
            data_id = created_data["id"]
        else:
            print(f"创建失败: {response.text}")
            return
        
        # 测试获取股票数据列表
        response = await client.get("/api/stock-data/")
        print(f"获取股票数据列表 - 状态码: {response.status_code}")
        if response.status_code == 200:
            data_list = response.json()
            print(f"股票数据列表: {len(data_list)} 条记录")
        
        # 测试按股票代码获取数据
        response = await client.get(f"/api/stock-data/by-code/000002")
        print(f"按代码获取数据 - 状态码: {response.status_code}")
        if response.status_code == 200:
            code_data = response.json()
            print(f"代码数据: {len(code_data)} 条记录")
        
        # 测试删除股票数据
        response = await client.delete(f"/api/stock-data/{data_id}")
        print(f"删除股票数据 - 状态码: {response.status_code}")
        
    print("✅ 股票数据CRUD测试完成\n")

async def test_monitor_crud():
    """测试监控列表CRUD操作"""
    print("🔍 测试监控列表CRUD操作...")
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # 先创建股票信息
        stock_info = {
            "code": "000003",
            "name": "国农科技",
            "market": "sz"
        }
        await client.post("/api/stocks/", json=stock_info)
        
        # 测试创建监控
        monitor_data = {
            "code": "000003",
            "priority": 8,
            "is_active": True
        }
        response = await client.post("/api/monitors/", json=monitor_data)
        print(f"创建监控 - 状态码: {response.status_code}")
        if response.status_code == 201:
            created_monitor = response.json()
            print(f"创建成功: {created_monitor['code']} - 优先级: {created_monitor['priority']}")
            monitor_id = created_monitor["id"]
        else:
            print(f"创建失败: {response.text}")
            return
        
        # 测试获取监控列表
        response = await client.get("/api/monitors/")
        print(f"获取监控列表 - 状态码: {response.status_code}")
        if response.status_code == 200:
            monitors = response.json()
            print(f"监控列表: {len(monitors)} 条记录")
        
        # 测试获取活跃监控
        response = await client.get("/api/monitors/active")
        print(f"获取活跃监控 - 状态码: {response.status_code}")
        if response.status_code == 200:
            active_monitors = response.json()
            print(f"活跃监控: {len(active_monitors)} 条记录")
        
        # 测试更新监控
        update_data = {"priority": 10, "is_active": False}
        response = await client.put(f"/api/monitors/{monitor_id}", json=update_data)
        print(f"更新监控 - 状态码: {response.status_code}")
        if response.status_code == 200:
            updated_monitor = response.json()
            print(f"更新成功: 优先级 {updated_monitor['priority']}, 活跃: {updated_monitor['is_active']}")
        
        # 测试删除监控
        response = await client.delete(f"/api/monitors/{monitor_id}")
        print(f"删除监控 - 状态码: {response.status_code}")
        
    print("✅ 监控列表CRUD测试完成\n")

async def test_batch_operations():
    """测试批量操作"""
    print("🔍 测试批量操作...")
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # 测试批量创建股票信息
        batch_stocks = [
            {"code": "000004", "name": "国华网安", "market": "sz"},
            {"code": "000005", "name": "世纪星源", "market": "sz"},
            {"code": "000006", "name": "深振业A", "market": "sz"}
        ]
        response = await client.post("/api/stocks/batch", json={"stocks": batch_stocks})
        print(f"批量创建股票 - 状态码: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"批量创建成功: {result['created_count']} 条记录")
        
        # 测试批量创建股票数据
        batch_data = []
        for i, code in enumerate(["000004", "000005", "000006"]):
            data = {
                "code": code,
                "name": batch_stocks[i]["name"],
                "price": 10.0 + i,
                "timestamp": datetime.now().isoformat()
            }
            batch_data.append(data)
        
        response = await client.post("/api/stock-data/batch", json={"data": batch_data})
        print(f"批量创建股票数据 - 状态码: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"批量创建数据成功: {result['created_count']} 条记录")
        
    print("✅ 批量操作测试完成\n")

async def test_error_handling():
    """测试错误处理"""
    print("🔍 测试错误处理...")
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # 测试获取不存在的股票
        response = await client.get("/api/stocks/99999")
        print(f"获取不存在股票 - 状态码: {response.status_code}")
        assert response.status_code == 404
        
        # 测试创建重复股票代码
        stock_data = {"code": "000001", "name": "测试股票", "market": "sz"}
        await client.post("/api/stocks/", json=stock_data)  # 第一次创建
        response = await client.post("/api/stocks/", json=stock_data)  # 重复创建
        print(f"创建重复股票 - 状态码: {response.status_code}")
        assert response.status_code == 400
        
        # 测试无效的股票代码格式
        invalid_data = {"code": "", "name": "无效股票", "market": "sz"}
        response = await client.post("/api/stocks/", json=invalid_data)
        print(f"无效股票代码 - 状态码: {response.status_code}")
        assert response.status_code == 422
        
    print("✅ 错误处理测试完成\n")

async def main():
    """主测试函数"""
    print("🚀 开始API集成测试...\n")
    
    try:
        await test_health_check()
        await test_stock_crud()
        await test_stock_data_crud()
        await test_monitor_crud()
        await test_batch_operations()
        await test_error_handling()
        
        print("🎉 所有API测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())