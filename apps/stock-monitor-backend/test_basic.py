#!/usr/bin/env python3
"""
基础测试脚本 - 不依赖数据库的基本功能测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
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

def test_app_creation():
    """测试应用创建"""
    print("=== 应用创建测试 ===")
    
    try:
        from app.main import app
        print("✅ FastAPI应用创建成功")
        print(f"✅ 应用标题: {app.title}")
        print(f"✅ 应用版本: {app.version}")
        return True
    except Exception as e:
        print(f"❌ FastAPI应用创建失败: {e}")
        return False

def test_config():
    """测试配置加载"""
    print("=== 配置加载测试 ===")
    
    try:
        from app.config.settings import get_settings
        settings = get_settings()
        print("✅ 配置加载成功")
        print(f"✅ 应用名称: {settings.app_name}")
        print(f"✅ 应用版本: {settings.app_version}")
        print(f"✅ 环境: {settings.environment}")
        print(f"✅ 主机: {settings.host}")
        print(f"✅ 端口: {settings.port}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_schemas():
    """测试数据模型"""
    print("=== 数据模型测试 ===")
    
    try:
        from app.api.schemas import StockInfoCreate, BaseResponse, HealthResponse
        from datetime import datetime
        
        # 测试股票信息创建模型
        stock_data = StockInfoCreate(
            stock_code="000001",
            stock_name="平安银行",
            market="SZ",
            industry="银行"
        )
        print("✅ StockInfoCreate模型验证成功")
        
        # 测试基础响应模型
        response = BaseResponse(
            success=True,
            message="测试成功",
            data={"test": "data"}
        )
        print("✅ BaseResponse模型验证成功")
        
        # 测试健康检查响应模型
        health = HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            uptime=123.45
        )
        print("✅ HealthResponse模型验证成功")
        
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_basic_api():
    """测试基础API（不依赖数据库）"""
    print("=== 基础API测试 ===")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # 测试基础健康检查（不依赖数据库）
        response = client.get("/api/v1/health")
        if response.status_code == 200:
            print("✅ 基础健康检查API成功")
            data = response.json()
            print(f"   状态: {data.get('data', {}).get('status', 'unknown')}")
        else:
            print(f"❌ 基础健康检查API失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
        
        # 测试存活检查
        response = client.get("/api/v1/health/liveness")
        if response.status_code == 200:
            print("✅ 存活检查API成功")
        else:
            print(f"❌ 存活检查API失败: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 基础API测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始基础功能测试...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_schemas,
        test_app_creation,
        test_basic_api
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基础功能测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)