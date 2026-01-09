#!/usr/bin/env python3
"""
简化测试脚本 - 验证核心功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def test_basic_functionality():
    """测试基础功能"""
    client = TestClient(app)
    
    print("=== 基础功能测试 ===")
    
    # 1. 健康检查
    print("1. 测试健康检查...")
    response = client.get("/api/v1/health")
    if response.status_code == 200:
        print("✅ 健康检查通过")
    else:
        print(f"❌ 健康检查失败: {response.status_code}")
        return False
    
    # 2. 创建股票信息
    print("2. 测试创建股票信息...")
    stock_data = {
        "code": "TEST01",
        "name": "测试股票",
        "market": "SZ",
        "industry": "测试"
    }
    response = client.post("/api/v1/stocks/info", json=stock_data)
    if response.status_code == 200:
        print("✅ 创建股票信息成功")
    else:
        print(f"❌ 创建股票信息失败: {response.status_code}")
        print(f"响应: {response.text}")
        return False
    
    # 3. 查询股票信息
    print("3. 测试查询股票信息...")
    response = client.get("/api/v1/stocks/info/TEST01")
    if response.status_code == 200:
        print("✅ 查询股票信息成功")
    else:
        print(f"❌ 查询股票信息失败: {response.status_code}")
        return False
    
    # 4. 添加监控
    print("4. 测试添加监控...")
    monitor_data = {
        "stock_code": "TEST01",
        "priority": 1
    }
    response = client.post("/api/v1/monitors", json=monitor_data)
    if response.status_code == 200:
        print("✅ 添加监控成功")
    else:
        print(f"❌ 添加监控失败: {response.status_code}")
        print(f"响应: {response.text}")
        return False
    
    # 5. 提交股票数据
    print("5. 测试提交股票数据...")
    data = {
        "code": "TEST01",
        "name": "测试股票",
        "current_price": 12.50,
        "volume": 1000000
    }
    response = client.post("/api/v1/stocks/data", json=data)
    if response.status_code == 200:
        print("✅ 提交股票数据成功")
    else:
        print(f"❌ 提交股票数据失败: {response.status_code}")
        print(f"响应: {response.text}")
        return False
    
    # 6. 清理测试数据
    print("6. 清理测试数据...")
    client.delete("/api/v1/monitors/TEST01")
    client.delete("/api/v1/stocks/info/TEST01")
    print("✅ 清理完成")
    
    return True

def test_import_modules():
    """测试模块导入"""
    print("=== 模块导入测试 ===")
    
    try:
        from app.models import stock
        print("✅ 模型模块导入成功")
    except Exception as e:
        print(f"❌ 模型模块导入失败: {e}")
        return False
    
    try:
        from app.api import health_controller, stock_controller, monitor_controller
        print("✅ 控制器模块导入成功")
    except Exception as e:
        print(f"❌ 控制器模块导入失败: {e}")
        return False
    
    try:
        from app.services import stock_service, monitor_service
        print("✅ 服务模块导入成功")
    except Exception as e:
        print(f"❌ 服务模块导入失败: {e}")
        return False
    
    try:
        from app.repositories import stock_repository, monitor_repository
        print("✅ Repository模块导入成功")
    except Exception as e:
        print(f"❌ Repository模块导入失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("开始简化测试...")
    
    # 测试模块导入
    if not test_import_modules():
        print("\n❌ 模块导入测试失败")
        return False
    
    # 测试基础功能
    if not test_basic_functionality():
        print("\n❌ 基础功能测试失败")
        return False
    
    print("\n🎉 所有测试通过！")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)