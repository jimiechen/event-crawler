#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API控制器测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json


class TestStockAPI:
    """股票API测试"""
    
    @pytest.mark.asyncio
    async def test_create_stock_info(self, test_client):
        """测试创建股票信息"""
        stock_data = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stock_code"] == "000001"
    
    @pytest.mark.asyncio
    async def test_get_stock_info(self, test_client, sample_stock_info):
        """测试获取股票信息"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 获取股票信息
        response = await test_client.get("/api/stocks/info/000001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stock_code"] == "000001"
    
    @pytest.mark.asyncio
    async def test_get_stock_info_not_found(self, test_client):
        """测试获取不存在的股票信息"""
        response = await test_client.get("/api/stocks/info/999999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "不存在" in data["message"]
    
    @pytest.mark.asyncio
    async def test_update_stock_info(self, test_client, sample_stock_info):
        """测试更新股票信息"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 更新股票信息
        update_data = {
            "stock_name": "平安银行(更新)",
            "is_active": False
        }
        
        response = await test_client.put("/api/stocks/info/000001", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stock_name"] == "平安银行(更新)"
        assert data["data"]["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_submit_stock_data(self, test_client, sample_stock_info):
        """测试提交股票数据"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 提交股票数据
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000,
            "turnover": 12500000.0,
            "high": 12.80,
            "low": 12.20,
            "open": 12.30,
            "close": 12.50
        }
        
        response = await test_client.post("/api/stocks/data", json=stock_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stock_code"] == "000001"
    
    @pytest.mark.asyncio
    async def test_batch_submit_stock_data(self, test_client, sample_stock_info):
        """测试批量提交股票数据"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 批量提交数据
        batch_data = {
            "data_list": [
                {
                    "stock_code": "000001",
                    "price": 12.50,
                    "volume": 1000000
                },
                {
                    "stock_code": "000001",
                    "price": 12.60,
                    "volume": 1100000
                }
            ]
        }
        
        response = await test_client.post("/api/stocks/data/batch", json=batch_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 2
    
    @pytest.mark.asyncio
    async def test_get_historical_data(self, test_client, sample_stock_info):
        """测试获取历史数据"""
        # 先创建股票和数据
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        await test_client.post("/api/stocks/data", json=stock_data)
        
        # 获取历史数据
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        response = await test_client.get(
            f"/api/stocks/data/000001/history?start_time={start_time}&end_time={end_time}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_get_latest_data(self, test_client, sample_stock_info):
        """测试获取最新数据"""
        # 先创建股票和数据
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        await test_client.post("/api/stocks/data", json=stock_data)
        
        # 获取最新数据
        response = await test_client.get("/api/stocks/data/000001/latest")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stock_code"] == "000001"
    
    @pytest.mark.asyncio
    async def test_get_stock_statistics(self, test_client):
        """测试获取股票统计"""
        response = await test_client.get("/api/stocks/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_stocks" in data["data"]
        assert "active_stocks" in data["data"]


class TestMonitorAPI:
    """监控API测试"""
    
    @pytest.mark.asyncio
    async def test_add_monitor(self, test_client, sample_stock_info):
        """测试添加监控"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 添加监控
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stock_code"] == "000001"
    
    @pytest.mark.asyncio
    async def test_add_monitor_stock_not_exists(self, test_client):
        """测试添加监控（股票不存在）"""
        monitor_data = {
            "stock_code": "999999",
            "priority": 5,
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "不存在" in data["message"]
    
    @pytest.mark.asyncio
    async def test_get_monitor_list(self, test_client, sample_stock_info, sample_monitor):
        """测试获取监控列表"""
        # 先创建股票和监控
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        await test_client.post("/api/monitors", json=sample_monitor)
        
        # 获取监控列表
        response = await test_client.get("/api/monitors")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_get_monitor_list_with_stock_info(self, test_client, sample_stock_info, sample_monitor):
        """测试获取监控列表（包含股票信息）"""
        # 先创建股票和监控
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        await test_client.post("/api/monitors", json=sample_monitor)
        
        # 获取监控列表（包含股票信息）
        response = await test_client.get("/api/monitors?include_stock_info=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_update_monitor_priority(self, test_client, sample_stock_info, sample_monitor):
        """测试更新监控优先级"""
        # 先创建股票和监控
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        await test_client.post("/api/monitors", json=sample_monitor)
        
        # 更新优先级
        update_data = {"priority": 8}
        
        response = await test_client.put("/api/monitors/000001/priority", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["priority"] == 8
    
    @pytest.mark.asyncio
    async def test_activate_monitor(self, test_client, sample_stock_info):
        """测试激活监控"""
        # 先创建股票和非活跃监控
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": False
        }
        await test_client.post("/api/monitors", json=monitor_data)
        
        # 激活监控
        response = await test_client.post("/api/monitors/000001/activate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_deactivate_monitor(self, test_client, sample_stock_info, sample_monitor):
        """测试停用监控"""
        # 先创建股票和监控
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        await test_client.post("/api/monitors", json=sample_monitor)
        
        # 停用监控
        response = await test_client.post("/api/monitors/000001/deactivate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_remove_monitor(self, test_client, sample_stock_info, sample_monitor):
        """测试移除监控"""
        # 先创建股票和监控
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        await test_client.post("/api/monitors", json=sample_monitor)
        
        # 移除监控
        response = await test_client.delete("/api/monitors/000001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_batch_add_monitors(self, test_client, sample_stock_info):
        """测试批量添加监控"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 批量添加监控
        batch_data = {
            "monitors": [
                {"stock_code": "000001", "priority": 5},
                {"stock_code": "000001", "priority": 8}  # 重复的股票代码
            ]
        }
        
        response = await test_client.post("/api/monitors/batch", json=batch_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 2
    
    @pytest.mark.asyncio
    async def test_get_high_priority_monitors(self, test_client, sample_stock_info):
        """测试获取高优先级监控"""
        # 先创建股票和不同优先级的监控
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        monitors = [
            {"stock_code": "000001", "priority": 3},
            {"stock_code": "000001", "priority": 8}
        ]
        
        for monitor in monitors:
            # 为了避免重复，我们需要先删除之前的监控
            await test_client.delete(f"/api/monitors/{monitor['stock_code']}")
            await test_client.post("/api/monitors", json=monitor)
        
        # 获取高优先级监控
        response = await test_client.get("/api/monitors/high-priority?min_priority=7")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_monitor_statistics(self, test_client):
        """测试获取监控统计"""
        response = await test_client.get("/api/monitors/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_monitors" in data["data"]
        assert "active_monitors" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_alerts(self, test_client):
        """测试获取告警"""
        response = await test_client.get("/api/monitors/alerts")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestHealthAPI:
    """健康检查API测试"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_client):
        """测试基础健康检查"""
        response = await test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_detailed_health_check(self, test_client):
        """测试详细健康检查"""
        response = await test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data["checks"]
        assert "services" in data["checks"]
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, test_client):
        """测试数据库健康检查"""
        response = await test_client.get("/health/database")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "connection" in data
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, test_client):
        """测试就绪检查"""
        response = await test_client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, test_client):
        """测试存活检查"""
        response = await test_client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "uptime" in data


class TestAPIValidation:
    """API验证测试"""
    
    @pytest.mark.asyncio
    async def test_invalid_stock_code_format(self, test_client):
        """测试无效股票代码格式"""
        stock_data = {
            "stock_code": "invalid",  # 无效格式
            "stock_name": "测试股票",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "validation error" in data["detail"][0]["type"]
    
    @pytest.mark.asyncio
    async def test_invalid_market_value(self, test_client):
        """测试无效市场值"""
        stock_data = {
            "stock_code": "000001",
            "stock_name": "测试股票",
            "market": "INVALID",  # 无效市场
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_negative_price(self, test_client, sample_stock_info):
        """测试负价格"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 提交负价格数据
        stock_data = {
            "stock_code": "000001",
            "price": -12.50,  # 负价格
            "volume": 1000000
        }
        
        response = await test_client.post("/api/stocks/data", json=stock_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_priority_range(self, test_client, sample_stock_info):
        """测试无效优先级范围"""
        # 先创建股票
        await test_client.post("/api/stocks/info", json=sample_stock_info)
        
        # 添加无效优先级的监控
        monitor_data = {
            "stock_code": "000001",
            "priority": 15,  # 超出范围（1-10）
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client):
        """测试缺少必需字段"""
        # 缺少stock_name字段
        stock_data = {
            "stock_code": "000001",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_data)
        
        assert response.status_code == 422
        data = response.json()
        assert any("stock_name" in str(error) for error in data["detail"])


class TestAPIErrorHandling:
    """API错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_duplicate_stock_creation(self, test_client, sample_stock_info):
        """测试重复创建股票"""
        # 创建股票
        response1 = await test_client.post("/api/stocks/info", json=sample_stock_info)
        assert response1.status_code == 201
        
        # 尝试重复创建
        response2 = await test_client.post("/api/stocks/info", json=sample_stock_info)
        assert response2.status_code == 400
        data = response2.json()
        assert data["success"] is False
        assert "已存在" in data["message"]
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_stock(self, test_client):
        """测试更新不存在的股票"""
        update_data = {
            "stock_name": "更新的股票名",
            "is_active": False
        }
        
        response = await test_client.put("/api/stocks/info/999999", json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "不存在" in data["message"]
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_monitor(self, test_client):
        """测试移除不存在的监控"""
        response = await test_client.delete("/api/monitors/999999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "不存在" in data["message"]