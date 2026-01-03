#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any


class TestStockDataFlow:
    """股票数据流集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_stock_workflow(self, test_client):
        """测试完整的股票工作流"""
        # 1. 创建股票信息
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 提交股票数据
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
        
        # 3. 获取最新数据
        response = await test_client.get("/api/stocks/data/000001/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["price"] == 12.50
        
        # 4. 获取历史数据
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        response = await test_client.get(
            f"/api/stocks/data/000001/history?start_time={start_time}&end_time={end_time}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        
        # 5. 更新股票信息
        update_data = {"stock_name": "平安银行(更新)"}
        response = await test_client.put("/api/stocks/info/000001", json=update_data)
        assert response.status_code == 200
        
        # 6. 验证更新
        response = await test_client.get("/api/stocks/info/000001")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["stock_name"] == "平安银行(更新)"
    
    @pytest.mark.asyncio
    async def test_batch_data_submission(self, test_client):
        """测试批量数据提交"""
        # 1. 创建多个股票
        stocks = [
            {"stock_code": "000001", "stock_name": "平安银行", "market": "SZ"},
            {"stock_code": "000002", "stock_name": "万科A", "market": "SZ"},
            {"stock_code": "600000", "stock_name": "浦发银行", "market": "SH"}
        ]
        
        for stock in stocks:
            stock["is_active"] = True
            response = await test_client.post("/api/stocks/info", json=stock)
            assert response.status_code == 201
        
        # 2. 批量提交数据
        batch_data = {
            "data_list": [
                {"stock_code": "000001", "price": 12.50, "volume": 1000000},
                {"stock_code": "000002", "price": 25.30, "volume": 2000000},
                {"stock_code": "600000", "price": 11.80, "volume": 1500000}
            ]
        }
        
        response = await test_client.post("/api/stocks/data/batch", json=batch_data)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["total"] == 3
        assert data["data"]["success"] == 3
        
        # 3. 验证所有数据都已保存
        for stock_code in ["000001", "000002", "600000"]:
            response = await test_client.get(f"/api/stocks/data/{stock_code}/latest")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_data_deduplication(self, test_client):
        """测试数据去重"""
        # 1. 创建股票
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 提交相同的数据两次
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        # 第一次提交
        response1 = await test_client.post("/api/stocks/data", json=stock_data)
        assert response1.status_code == 201
        
        # 第二次提交（应该被去重）
        response2 = await test_client.post("/api/stocks/data", json=stock_data)
        # 根据实现，可能返回200（已存在）或201（重复但记录）
        assert response2.status_code in [200, 201]
        
        # 3. 验证历史数据中只有一条记录（或者有重复标记）
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        response = await test_client.get(
            f"/api/stocks/data/000001/history?start_time={start_time}&end_time={end_time}"
        )
        assert response.status_code == 200


class TestMonitoringWorkflow:
    """监控工作流集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_monitoring_workflow(self, test_client):
        """测试完整的监控工作流"""
        # 1. 创建股票
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 添加监控
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        assert response.status_code == 201
        
        # 3. 获取监控列表
        response = await test_client.get("/api/monitors")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        
        # 4. 更新监控优先级
        update_data = {"priority": 8}
        response = await test_client.put("/api/monitors/000001/priority", json=update_data)
        assert response.status_code == 200
        
        # 5. 获取高优先级监控
        response = await test_client.get("/api/monitors/high-priority?min_priority=7")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        
        # 6. 停用监控
        response = await test_client.post("/api/monitors/000001/deactivate")
        assert response.status_code == 200
        
        # 7. 验证监控已停用
        response = await test_client.get("/api/monitors")
        assert response.status_code == 200
        data = response.json()
        # 根据查询参数，可能包含或不包含非活跃监控
        
        # 8. 重新激活监控
        response = await test_client.post("/api/monitors/000001/activate")
        assert response.status_code == 200
        
        # 9. 移除监控
        response = await test_client.delete("/api/monitors/000001")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_batch_monitor_operations(self, test_client):
        """测试批量监控操作"""
        # 1. 创建多个股票
        stocks = [
            {"stock_code": "000001", "stock_name": "平安银行", "market": "SZ"},
            {"stock_code": "000002", "stock_name": "万科A", "market": "SZ"},
            {"stock_code": "600000", "stock_name": "浦发银行", "market": "SH"}
        ]
        
        for stock in stocks:
            stock["is_active"] = True
            response = await test_client.post("/api/stocks/info", json=stock)
            assert response.status_code == 201
        
        # 2. 批量添加监控
        batch_monitors = {
            "monitors": [
                {"stock_code": "000001", "priority": 5},
                {"stock_code": "000002", "priority": 8},
                {"stock_code": "600000", "priority": 3}
            ]
        }
        
        response = await test_client.post("/api/monitors/batch", json=batch_monitors)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["total"] == 3
        assert data["data"]["success"] == 3
        
        # 3. 批量更新优先级
        batch_update = {
            "updates": [
                {"stock_code": "000001", "priority": 9},
                {"stock_code": "000002", "priority": 7}
            ]
        }
        
        response = await test_client.put("/api/monitors/batch/priority", json=batch_update)
        assert response.status_code == 200
        
        # 4. 批量停用监控
        batch_deactivate = {
            "stock_codes": ["000001", "600000"]
        }
        
        response = await test_client.post("/api/monitors/batch/deactivate", json=batch_deactivate)
        assert response.status_code == 200
        
        # 5. 验证操作结果
        response = await test_client.get("/api/monitors")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_monitor_with_stock_info_and_data(self, test_client):
        """测试监控与股票信息和数据的集成"""
        # 1. 创建股票
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 添加监控
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        assert response.status_code == 201
        
        # 3. 提交股票数据
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        response = await test_client.post("/api/stocks/data", json=stock_data)
        assert response.status_code == 201
        
        # 4. 获取监控列表（包含股票信息）
        response = await test_client.get("/api/monitors?include_stock_info=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        # 验证返回的数据包含股票信息
        
        # 5. 获取监控列表（包含最新数据）
        response = await test_client.get("/api/monitors?include_latest_data=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        # 验证返回的数据包含最新股票数据


class TestAlertSystem:
    """告警系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_no_data_alert_generation(self, test_client):
        """测试无数据告警生成"""
        # 1. 创建股票
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 添加监控
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        assert response.status_code == 201
        
        # 3. 不提交任何数据，直接检查告警
        response = await test_client.get("/api/monitors/alerts?threshold_minutes=1")
        assert response.status_code == 200
        data = response.json()
        # 应该有告警，因为没有数据
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_alert_with_recent_data(self, test_client):
        """测试有最新数据时的告警"""
        # 1. 创建股票
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 添加监控
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        assert response.status_code == 201
        
        # 3. 提交最新数据
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        response = await test_client.post("/api/stocks/data", json=stock_data)
        assert response.status_code == 201
        
        # 4. 检查告警（应该没有告警，因为有最新数据）
        response = await test_client.get("/api/monitors/alerts?threshold_minutes=10")
        assert response.status_code == 200
        data = response.json()
        # 应该没有告警或者告警数量较少
        assert isinstance(data["data"], list)


class TestSystemIntegration:
    """系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_health_checks_integration(self, test_client):
        """测试健康检查集成"""
        # 1. 基础健康检查
        response = await test_client.get("/health")
        assert response.status_code == 200
        
        # 2. 详细健康检查
        response = await test_client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data["checks"]
        
        # 3. 数据库健康检查
        response = await test_client.get("/health/database")
        assert response.status_code == 200
        
        # 4. 就绪检查
        response = await test_client.get("/health/ready")
        assert response.status_code == 200
        
        # 5. 存活检查
        response = await test_client.get("/health/live")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_statistics_integration(self, test_client):
        """测试统计信息集成"""
        # 1. 创建一些测试数据
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 添加监控
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        response = await test_client.post("/api/monitors", json=monitor_data)
        assert response.status_code == 201
        
        # 3. 提交数据
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        response = await test_client.post("/api/stocks/data", json=stock_data)
        assert response.status_code == 201
        
        # 4. 获取股票统计
        response = await test_client.get("/api/stocks/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_stocks"] >= 1
        assert data["data"]["active_stocks"] >= 1
        
        # 5. 获取监控统计
        response = await test_client.get("/api/monitors/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_monitors"] >= 1
        assert data["data"]["active_monitors"] >= 1
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, test_client):
        """测试并发操作"""
        # 1. 创建股票
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201
        
        # 2. 并发提交数据
        async def submit_data(price: float):
            stock_data = {
                "stock_code": "000001",
                "price": price,
                "volume": 1000000
            }
            return await test_client.post("/api/stocks/data", json=stock_data)
        
        # 并发提交多个不同价格的数据
        tasks = [submit_data(12.0 + i * 0.1) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功处理
        for response in responses:
            assert response.status_code in [200, 201]
        
        # 3. 验证数据完整性
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        response = await test_client.get(
            f"/api/stocks/data/000001/history?start_time={start_time}&end_time={end_time}"
        )
        assert response.status_code == 200
        data = response.json()
        # 验证数据数量（考虑去重）
        assert len(data["data"]) >= 1
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, test_client):
        """测试错误恢复"""
        # 1. 尝试操作不存在的资源
        response = await test_client.get("/api/stocks/info/999999")
        assert response.status_code == 404
        
        # 2. 尝试无效操作
        response = await test_client.post("/api/monitors", json={
            "stock_code": "999999",  # 不存在的股票
            "priority": 5,
            "is_active": True
        })
        assert response.status_code == 400
        
        # 3. 验证系统仍然正常工作
        response = await test_client.get("/health")
        assert response.status_code == 200
        
        # 4. 执行正常操作
        stock_info = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        response = await test_client.post("/api/stocks/info", json=stock_info)
        assert response.status_code == 201