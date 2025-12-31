#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service层测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.services.stock_service import StockService
from app.services.monitor_service import MonitorService
from app.services.data_dedup_service import DataDedupService


class TestStockService:
    """股票服务测试"""
    
    @pytest.fixture
    def mock_stock_repo(self):
        """模拟股票Repository"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_data_repo(self):
        """模拟股票数据Repository"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_dedup_service(self):
        """模拟去重服务"""
        return AsyncMock()
    
    @pytest.fixture
    def stock_service(self, test_session, mock_dedup_service):
        """股票服务实例"""
        return StockService(test_session, mock_dedup_service)
    
    @pytest.mark.asyncio
    async def test_get_stock_info(self, stock_service, mock_stock_repo):
        """测试获取股票信息"""
        # 模拟返回数据
        mock_stock = MagicMock()
        mock_stock.stock_code = "000001"
        mock_stock.stock_name = "平安银行"
        mock_stock_repo.find_by_code.return_value = mock_stock
        
        with patch.object(stock_service, 'stock_repo', mock_stock_repo):
            result = await stock_service.get_stock_info("000001")
            
            assert result is not None
            assert result.stock_code == "000001"
            mock_stock_repo.find_by_code.assert_called_once_with("000001")
    
    @pytest.mark.asyncio
    async def test_create_stock_info(self, stock_service, mock_stock_repo):
        """测试创建股票信息"""
        stock_data = {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market": "SZ",
            "is_active": True
        }
        
        mock_stock = MagicMock()
        mock_stock.stock_code = "000001"
        mock_stock_repo.create.return_value = mock_stock
        
        with patch.object(stock_service, 'stock_repo', mock_stock_repo):
            result = await stock_service.create_stock_info(stock_data)
            
            assert result.stock_code == "000001"
            mock_stock_repo.create.assert_called_once_with(stock_data)
    
    @pytest.mark.asyncio
    async def test_submit_stock_data_with_deduplication(self, stock_service, mock_data_repo, mock_dedup_service):
        """测试提交股票数据（含去重）"""
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        # 模拟去重服务返回非重复
        mock_dedup_service.is_duplicate.return_value = False
        
        # 模拟数据创建
        mock_data = MagicMock()
        mock_data.id = 1
        mock_data_repo.create.return_value = mock_data
        
        with patch.object(stock_service, 'data_repo', mock_data_repo):
            result = await stock_service.submit_stock_data(stock_data)
            
            assert result.id == 1
            mock_dedup_service.is_duplicate.assert_called_once()
            mock_data_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_duplicate_stock_data(self, stock_service, mock_data_repo, mock_dedup_service):
        """测试提交重复股票数据"""
        stock_data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        # 模拟去重服务返回重复
        mock_dedup_service.is_duplicate.return_value = True
        
        with patch.object(stock_service, 'data_repo', mock_data_repo):
            result = await stock_service.submit_stock_data(stock_data)
            
            assert result is None  # 重复数据不应该被保存
            mock_dedup_service.is_duplicate.assert_called_once()
            mock_data_repo.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_batch_submit_stock_data(self, stock_service, mock_data_repo, mock_dedup_service):
        """测试批量提交股票数据"""
        batch_data = [
            {"stock_code": "000001", "price": 12.50, "volume": 1000000},
            {"stock_code": "000002", "price": 15.30, "volume": 2000000},
            {"stock_code": "000003", "price": 8.90, "volume": 500000}
        ]
        
        # 模拟去重结果：第一个和第三个不重复，第二个重复
        mock_dedup_service.is_duplicate.side_effect = [False, True, False]
        
        # 模拟数据创建
        mock_data_repo.create.side_effect = [
            MagicMock(id=1),  # 第一个数据
            MagicMock(id=3)   # 第三个数据
        ]
        
        with patch.object(stock_service, 'data_repo', mock_data_repo):
            result = await stock_service.batch_submit_stock_data(batch_data)
            
            assert result["total"] == 3
            assert result["success"] == 2
            assert result["duplicates"] == 1
            assert len(result["created_ids"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_historical_data(self, stock_service, mock_data_repo):
        """测试获取历史数据"""
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        
        mock_data_list = [MagicMock(id=i) for i in range(5)]
        mock_data_repo.find_by_code_and_time_range.return_value = mock_data_list
        
        with patch.object(stock_service, 'data_repo', mock_data_repo):
            result = await stock_service.get_historical_data("000001", start_time, end_time)
            
            assert len(result) == 5
            mock_data_repo.find_by_code_and_time_range.assert_called_once_with(
                "000001", start_time, end_time
            )
    
    @pytest.mark.asyncio
    async def test_get_stock_statistics(self, stock_service, mock_stock_repo, mock_data_repo):
        """测试获取股票统计"""
        # 模拟股票总数
        mock_stock_repo.count_all.return_value = 100
        mock_stock_repo.count_active.return_value = 85
        
        # 模拟数据统计
        mock_data_repo.count_today.return_value = 5000
        mock_data_repo.count_total.return_value = 1000000
        
        with patch.object(stock_service, 'stock_repo', mock_stock_repo), \
             patch.object(stock_service, 'data_repo', mock_data_repo):
            
            stats = await stock_service.get_stock_statistics()
            
            assert stats["total_stocks"] == 100
            assert stats["active_stocks"] == 85
            assert stats["today_data_count"] == 5000
            assert stats["total_data_count"] == 1000000


class TestMonitorService:
    """监控服务测试"""
    
    @pytest.fixture
    def mock_monitor_repo(self):
        """模拟监控Repository"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_stock_repo(self):
        """模拟股票Repository"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_data_repo(self):
        """模拟股票数据Repository"""
        return AsyncMock()
    
    @pytest.fixture
    def monitor_service(self, test_session):
        """监控服务实例"""
        return MonitorService(test_session)
    
    @pytest.mark.asyncio
    async def test_add_monitor(self, monitor_service, mock_monitor_repo, mock_stock_repo):
        """测试添加监控"""
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        # 模拟股票存在
        mock_stock = MagicMock()
        mock_stock_repo.find_by_code.return_value = mock_stock
        
        # 模拟监控不存在
        mock_monitor_repo.find_by_stock_code.return_value = None
        
        # 模拟创建监控
        mock_monitor = MagicMock()
        mock_monitor.stock_code = "000001"
        mock_monitor_repo.create.return_value = mock_monitor
        
        with patch.object(monitor_service, 'monitor_repo', mock_monitor_repo), \
             patch.object(monitor_service, 'stock_repo', mock_stock_repo):
            
            result = await monitor_service.add_monitor(monitor_data)
            
            assert result.stock_code == "000001"
            mock_monitor_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_monitor_stock_not_exists(self, monitor_service, mock_monitor_repo, mock_stock_repo):
        """测试添加监控（股票不存在）"""
        monitor_data = {
            "stock_code": "999999",
            "priority": 5,
            "is_active": True
        }
        
        # 模拟股票不存在
        mock_stock_repo.find_by_code.return_value = None
        
        with patch.object(monitor_service, 'monitor_repo', mock_monitor_repo), \
             patch.object(monitor_service, 'stock_repo', mock_stock_repo):
            
            with pytest.raises(ValueError, match="股票不存在"):
                await monitor_service.add_monitor(monitor_data)
    
    @pytest.mark.asyncio
    async def test_add_monitor_already_exists(self, monitor_service, mock_monitor_repo, mock_stock_repo):
        """测试添加监控（监控已存在）"""
        monitor_data = {
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        }
        
        # 模拟股票存在
        mock_stock = MagicMock()
        mock_stock_repo.find_by_code.return_value = mock_stock
        
        # 模拟监控已存在
        mock_monitor = MagicMock()
        mock_monitor_repo.find_by_stock_code.return_value = mock_monitor
        
        with patch.object(monitor_service, 'monitor_repo', mock_monitor_repo), \
             patch.object(monitor_service, 'stock_repo', mock_stock_repo):
            
            with pytest.raises(ValueError, match="监控已存在"):
                await monitor_service.add_monitor(monitor_data)
    
    @pytest.mark.asyncio
    async def test_get_monitor_list_with_stock_info(self, monitor_service, mock_monitor_repo, mock_stock_repo):
        """测试获取监控列表（包含股票信息）"""
        # 模拟监控列表
        mock_monitors = [
            MagicMock(stock_code="000001", priority=5),
            MagicMock(stock_code="000002", priority=8)
        ]
        mock_monitor_repo.find_all.return_value = mock_monitors
        
        # 模拟股票信息
        mock_stocks = {
            "000001": MagicMock(stock_name="平安银行", market="SZ"),
            "000002": MagicMock(stock_name="万科A", market="SZ")
        }
        mock_stock_repo.find_by_codes.return_value = list(mock_stocks.values())
        
        with patch.object(monitor_service, 'monitor_repo', mock_monitor_repo), \
             patch.object(monitor_service, 'stock_repo', mock_stock_repo):
            
            result = await monitor_service.get_monitor_list(include_stock_info=True)
            
            assert len(result) == 2
            mock_stock_repo.find_by_codes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_add_monitors(self, monitor_service, mock_monitor_repo, mock_stock_repo):
        """测试批量添加监控"""
        batch_data = [
            {"stock_code": "000001", "priority": 5},
            {"stock_code": "000002", "priority": 8},
            {"stock_code": "999999", "priority": 3}  # 不存在的股票
        ]
        
        # 模拟股票存在性检查
        mock_stock_repo.find_by_codes.return_value = [
            MagicMock(stock_code="000001"),
            MagicMock(stock_code="000002")
        ]
        
        # 模拟监控不存在
        mock_monitor_repo.find_by_codes.return_value = []
        
        # 模拟批量创建
        mock_monitor_repo.batch_create.return_value = [
            MagicMock(stock_code="000001"),
            MagicMock(stock_code="000002")
        ]
        
        with patch.object(monitor_service, 'monitor_repo', mock_monitor_repo), \
             patch.object(monitor_service, 'stock_repo', mock_stock_repo):
            
            result = await monitor_service.batch_add_monitors(batch_data)
            
            assert result["total"] == 3
            assert result["success"] == 2
            assert result["failed"] == 1
            assert "999999" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_generate_alerts(self, monitor_service, mock_monitor_repo, mock_data_repo):
        """测试生成告警"""
        # 模拟活跃监控
        mock_monitors = [
            MagicMock(stock_code="000001", priority=5),
            MagicMock(stock_code="000002", priority=8)
        ]
        mock_monitor_repo.find_active_monitors.return_value = mock_monitors
        
        # 模拟最新数据（000001有数据，000002无数据）
        now = datetime.now()
        mock_data_repo.find_latest_by_codes.return_value = [
            MagicMock(stock_code="000001", created_at=now - timedelta(minutes=5))
        ]
        
        with patch.object(monitor_service, 'monitor_repo', mock_monitor_repo), \
             patch.object(monitor_service, 'data_repo', mock_data_repo):
            
            alerts = await monitor_service.generate_alerts(threshold_minutes=10)
            
            assert len(alerts) == 1
            assert alerts[0]["stock_code"] == "000002"
            assert alerts[0]["alert_type"] == "no_data"


class TestDataDedupService:
    """数据去重服务测试"""
    
    @pytest.fixture
    def mock_dedup_repo(self):
        """模拟去重Repository"""
        return AsyncMock()
    
    @pytest.fixture
    def dedup_service(self, test_session):
        """去重服务实例"""
        return DataDedupService(test_session)
    
    def test_generate_data_hash(self, dedup_service):
        """测试生成数据哈希"""
        data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        hash1 = dedup_service.generate_data_hash(data)
        hash2 = dedup_service.generate_data_hash(data)
        
        # 相同数据应该生成相同哈希
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256哈希长度
        
        # 不同数据应该生成不同哈希
        data2 = data.copy()
        data2["price"] = 13.00
        hash3 = dedup_service.generate_data_hash(data2)
        assert hash1 != hash3
    
    @pytest.mark.asyncio
    async def test_is_duplicate_new_data(self, dedup_service, mock_dedup_repo):
        """测试检查重复（新数据）"""
        data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        # 模拟哈希不存在
        mock_dedup_repo.hash_exists.return_value = False
        mock_dedup_repo.create.return_value = MagicMock()
        
        with patch.object(dedup_service, 'dedup_repo', mock_dedup_repo):
            is_dup = await dedup_service.is_duplicate(data, "stock_data")
            
            assert is_dup is False
            mock_dedup_repo.hash_exists.assert_called_once()
            mock_dedup_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_is_duplicate_existing_data(self, dedup_service, mock_dedup_repo):
        """测试检查重复（已存在数据）"""
        data = {
            "stock_code": "000001",
            "price": 12.50,
            "volume": 1000000
        }
        
        # 模拟哈希已存在
        mock_dedup_repo.hash_exists.return_value = True
        mock_dedup_repo.create.return_value = MagicMock()
        
        with patch.object(dedup_service, 'dedup_repo', mock_dedup_repo):
            is_dup = await dedup_service.is_duplicate(data, "stock_data")
            
            assert is_dup is True
            mock_dedup_repo.hash_exists.assert_called_once()
            mock_dedup_repo.create.assert_called_once()  # 仍然记录重复日志
    
    @pytest.mark.asyncio
    async def test_batch_check_duplicates(self, dedup_service, mock_dedup_repo):
        """测试批量检查重复"""
        batch_data = [
            {"stock_code": "000001", "price": 12.50, "volume": 1000000},
            {"stock_code": "000002", "price": 15.30, "volume": 2000000},
            {"stock_code": "000003", "price": 8.90, "volume": 500000}
        ]
        
        # 模拟哈希存在性：第一个和第三个不存在，第二个存在
        mock_dedup_repo.hash_exists.side_effect = [False, True, False]
        mock_dedup_repo.batch_create.return_value = None
        
        with patch.object(dedup_service, 'dedup_repo', mock_dedup_repo):
            results = await dedup_service.batch_check_duplicates(batch_data, "stock_data")
            
            assert len(results) == 3
            assert results[0] is False  # 第一个不重复
            assert results[1] is True   # 第二个重复
            assert results[2] is False  # 第三个不重复
    
    @pytest.mark.asyncio
    async def test_get_dedup_statistics(self, dedup_service, mock_dedup_repo):
        """测试获取去重统计"""
        mock_stats = {
            "total_logs": 1000,
            "duplicate_count": 300,
            "unique_count": 700,
            "duplicate_rate": 0.3
        }
        mock_dedup_repo.get_dedup_statistics.return_value = mock_stats
        
        with patch.object(dedup_service, 'dedup_repo', mock_dedup_repo):
            stats = await dedup_service.get_dedup_statistics()
            
            assert stats == mock_stats
            mock_dedup_repo.get_dedup_statistics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, dedup_service, mock_dedup_repo):
        """测试清理旧日志"""
        mock_dedup_repo.cleanup_old_logs.return_value = 150
        
        with patch.object(dedup_service, 'dedup_repo', mock_dedup_repo):
            deleted_count = await dedup_service.cleanup_old_logs(days=30)
            
            assert deleted_count == 150
            mock_dedup_repo.cleanup_old_logs.assert_called_once_with(30)
    
    @pytest.mark.asyncio
    async def test_validate_data_integrity(self, dedup_service, mock_dedup_repo):
        """测试验证数据完整性"""
        # 模拟发现一些不一致的数据
        mock_dedup_repo.find_integrity_issues.return_value = [
            {"issue": "missing_hash", "count": 5},
            {"issue": "orphaned_log", "count": 2}
        ]
        
        with patch.object(dedup_service, 'dedup_repo', mock_dedup_repo):
            issues = await dedup_service.validate_data_integrity()
            
            assert len(issues) == 2
            assert issues[0]["issue"] == "missing_hash"
            assert issues[1]["count"] == 2