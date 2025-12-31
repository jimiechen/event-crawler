#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository层测试
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from app.models.stock import StockInfo, StockData, MonitorList, DataDedupLog
from app.repositories.stock_repository import StockRepository, StockDataRepository, DataDedupRepository
from app.repositories.monitor_repository import MonitorRepository


class TestStockRepository:
    """股票信息Repository测试"""
    
    @pytest.mark.asyncio
    async def test_create_stock(self, test_session, sample_stock_info):
        """测试创建股票"""
        repo = StockRepository(test_session)
        stock = await repo.create(sample_stock_info)
        
        assert stock.stock_code == "000001"
        assert stock.stock_name == "平安银行"
        assert stock.market == "SZ"
        assert stock.is_active is True
    
    @pytest.mark.asyncio
    async def test_find_by_code(self, test_session, sample_stock_info):
        """测试按代码查找股票"""
        repo = StockRepository(test_session)
        
        # 创建股票
        await repo.create(sample_stock_info)
        
        # 查找股票
        stock = await repo.find_by_code("000001")
        assert stock is not None
        assert stock.stock_code == "000001"
        
        # 查找不存在的股票
        not_found = await repo.find_by_code("999999")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_find_by_codes(self, test_session, multiple_stock_codes):
        """测试按代码列表查找股票"""
        repo = StockRepository(test_session)
        
        # 创建多个股票
        for code in multiple_stock_codes[:3]:
            await repo.create({
                "stock_code": code,
                "stock_name": f"股票{code}",
                "market": "SZ" if code.startswith("000") else "SH",
                "is_active": True
            })
        
        # 查找股票列表
        stocks = await repo.find_by_codes(multiple_stock_codes[:2])
        assert len(stocks) == 2
        assert all(stock.stock_code in multiple_stock_codes[:2] for stock in stocks)
    
    @pytest.mark.asyncio
    async def test_find_by_market(self, test_session):
        """测试按市场查找股票"""
        repo = StockRepository(test_session)
        
        # 创建不同市场的股票
        sz_stock = await repo.create({
            "stock_code": "000001",
            "stock_name": "深圳股票",
            "market": "SZ",
            "is_active": True
        })
        
        sh_stock = await repo.create({
            "stock_code": "600000",
            "stock_name": "上海股票",
            "market": "SH",
            "is_active": True
        })
        
        # 查找深圳市场股票
        sz_stocks = await repo.find_by_market("SZ")
        assert len(sz_stocks) == 1
        assert sz_stocks[0].market == "SZ"
        
        # 查找上海市场股票
        sh_stocks = await repo.find_by_market("SH")
        assert len(sh_stocks) == 1
        assert sh_stocks[0].market == "SH"
    
    @pytest.mark.asyncio
    async def test_find_active_stocks(self, test_session):
        """测试查找活跃股票"""
        repo = StockRepository(test_session)
        
        # 创建活跃和非活跃股票
        await repo.create({
            "stock_code": "000001",
            "stock_name": "活跃股票",
            "market": "SZ",
            "is_active": True
        })
        
        await repo.create({
            "stock_code": "000002",
            "stock_name": "非活跃股票",
            "market": "SZ",
            "is_active": False
        })
        
        # 查找活跃股票
        active_stocks = await repo.find_active_stocks()
        assert len(active_stocks) == 1
        assert active_stocks[0].is_active is True


class TestStockDataRepository:
    """股票数据Repository测试"""
    
    @pytest.mark.asyncio
    async def test_create_stock_data(self, test_session, sample_stock_data):
        """测试创建股票数据"""
        repo = StockDataRepository(test_session)
        data = await repo.create(sample_stock_data)
        
        assert data.stock_code == "000001"
        assert data.price == 12.50
        assert data.volume == 1000000
    
    @pytest.mark.asyncio
    async def test_find_by_code_and_time_range(self, test_session):
        """测试按代码和时间范围查找股票数据"""
        repo = StockDataRepository(test_session)
        
        # 创建不同时间的股票数据
        now = datetime.now()
        for i in range(5):
            data = {
                "stock_code": "000001",
                "price": 12.0 + i * 0.1,
                "volume": 1000000,
                "created_at": now - timedelta(hours=i)
            }
            await repo.create(data)
        
        # 查找最近3小时的数据
        start_time = now - timedelta(hours=3)
        end_time = now
        
        data_list = await repo.find_by_code_and_time_range("000001", start_time, end_time)
        assert len(data_list) >= 3  # 应该包含最近3小时的数据
    
    @pytest.mark.asyncio
    async def test_find_latest_by_code(self, test_session):
        """测试查找最新股票数据"""
        repo = StockDataRepository(test_session)
        
        # 创建多条数据
        for i in range(3):
            await repo.create({
                "stock_code": "000001",
                "price": 12.0 + i,
                "volume": 1000000
            })
        
        # 查找最新数据
        latest = await repo.find_latest_by_code("000001")
        assert latest is not None
        assert latest.price == 14.0  # 最后创建的数据
    
    @pytest.mark.asyncio
    async def test_find_recent_by_code(self, test_session):
        """测试查找最近股票数据"""
        repo = StockDataRepository(test_session)
        
        # 创建多条数据
        for i in range(10):
            await repo.create({
                "stock_code": "000001",
                "price": 12.0 + i,
                "volume": 1000000
            })
        
        # 查找最近5条数据
        recent_data = await repo.find_recent_by_code("000001", limit=5)
        assert len(recent_data) == 5
        # 数据应该按时间倒序排列
        assert recent_data[0].price > recent_data[-1].price
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, test_session):
        """测试清理旧数据"""
        repo = StockDataRepository(test_session)
        
        # 创建新旧数据
        now = datetime.now()
        
        # 创建旧数据（超过保留期）
        old_data = {
            "stock_code": "000001",
            "price": 10.0,
            "volume": 1000000,
            "created_at": now - timedelta(days=400)  # 超过365天
        }
        await repo.create(old_data)
        
        # 创建新数据
        new_data = {
            "stock_code": "000001",
            "price": 12.0,
            "volume": 1000000,
            "created_at": now
        }
        await repo.create(new_data)
        
        # 清理旧数据
        deleted_count = await repo.cleanup_old_data(days=365)
        assert deleted_count >= 1  # 至少删除了一条旧数据
        
        # 验证新数据仍然存在
        latest = await repo.find_latest_by_code("000001")
        assert latest is not None
        assert latest.price == 12.0


class TestMonitorRepository:
    """监控Repository测试"""
    
    @pytest.mark.asyncio
    async def test_create_monitor(self, test_session, sample_monitor):
        """测试创建监控"""
        repo = MonitorRepository(test_session)
        monitor = await repo.create(sample_monitor)
        
        assert monitor.stock_code == "000001"
        assert monitor.priority == 5
        assert monitor.is_active is True
    
    @pytest.mark.asyncio
    async def test_find_by_stock_code(self, test_session, sample_monitor):
        """测试按股票代码查找监控"""
        repo = MonitorRepository(test_session)
        
        # 创建监控
        await repo.create(sample_monitor)
        
        # 查找监控
        monitor = await repo.find_by_stock_code("000001")
        assert monitor is not None
        assert monitor.stock_code == "000001"
    
    @pytest.mark.asyncio
    async def test_find_active_monitors(self, test_session):
        """测试查找活跃监控"""
        repo = MonitorRepository(test_session)
        
        # 创建活跃和非活跃监控
        await repo.create({
            "stock_code": "000001",
            "priority": 5,
            "is_active": True
        })
        
        await repo.create({
            "stock_code": "000002",
            "priority": 3,
            "is_active": False
        })
        
        # 查找活跃监控
        active_monitors = await repo.find_active_monitors()
        assert len(active_monitors) == 1
        assert active_monitors[0].is_active is True
    
    @pytest.mark.asyncio
    async def test_find_high_priority_monitors(self, test_session):
        """测试查找高优先级监控"""
        repo = MonitorRepository(test_session)
        
        # 创建不同优先级的监控
        priorities = [3, 7, 9, 2, 8]
        for i, priority in enumerate(priorities):
            await repo.create({
                "stock_code": f"00000{i+1}",
                "priority": priority,
                "is_active": True
            })
        
        # 查找优先级>=7的监控
        high_priority = await repo.find_high_priority_monitors(min_priority=7)
        assert len(high_priority) == 3  # 优先级7, 9, 8的监控
        assert all(monitor.priority >= 7 for monitor in high_priority)
    
    @pytest.mark.asyncio
    async def test_get_monitor_codes(self, test_session):
        """测试获取监控股票代码"""
        repo = MonitorRepository(test_session)
        
        # 创建多个监控
        codes = ["000001", "000002", "600000"]
        for code in codes:
            await repo.create({
                "stock_code": code,
                "priority": 5,
                "is_active": True
            })
        
        # 获取监控代码
        monitor_codes = await repo.get_monitor_codes(active_only=True)
        assert len(monitor_codes) == 3
        assert set(monitor_codes) == set(codes)


class TestDataDedupRepository:
    """数据去重Repository测试"""
    
    @pytest.mark.asyncio
    async def test_create_dedup_log(self, test_session):
        """测试创建去重日志"""
        repo = DataDedupRepository(test_session)
        
        log_data = {
            "data_hash": "test_hash_123",
            "stock_code": "000001",
            "data_type": "stock_data",
            "is_duplicate": False
        }
        
        log = await repo.create(log_data)
        assert log.data_hash == "test_hash_123"
        assert log.is_duplicate is False
    
    @pytest.mark.asyncio
    async def test_hash_exists(self, test_session):
        """测试哈希是否存在"""
        repo = DataDedupRepository(test_session)
        
        # 创建去重日志
        await repo.create({
            "data_hash": "existing_hash",
            "stock_code": "000001",
            "data_type": "stock_data",
            "is_duplicate": False
        })
        
        # 检查哈希是否存在
        exists = await repo.hash_exists("existing_hash")
        assert exists is True
        
        not_exists = await repo.hash_exists("non_existing_hash")
        assert not_exists is False
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, test_session):
        """测试清理旧日志"""
        repo = DataDedupRepository(test_session)
        
        # 创建新旧日志
        now = datetime.now()
        
        # 创建旧日志
        old_log = {
            "data_hash": "old_hash",
            "stock_code": "000001",
            "data_type": "stock_data",
            "is_duplicate": False,
            "created_at": now - timedelta(days=40)  # 超过30天
        }
        await repo.create(old_log)
        
        # 创建新日志
        new_log = {
            "data_hash": "new_hash",
            "stock_code": "000001",
            "data_type": "stock_data",
            "is_duplicate": False,
            "created_at": now
        }
        await repo.create(new_log)
        
        # 清理旧日志
        deleted_count = await repo.cleanup_old_logs(days=30)
        assert deleted_count >= 1
        
        # 验证新日志仍然存在
        exists = await repo.hash_exists("new_hash")
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_get_dedup_statistics(self, test_session):
        """测试获取去重统计"""
        repo = DataDedupRepository(test_session)
        
        # 创建去重日志
        logs = [
            {"data_hash": f"hash_{i}", "stock_code": "000001", "data_type": "stock_data", "is_duplicate": i % 2 == 0}
            for i in range(10)
        ]
        
        for log_data in logs:
            await repo.create(log_data)
        
        # 获取统计信息
        stats = await repo.get_dedup_statistics()
        
        assert stats["total_logs"] == 10
        assert stats["duplicate_count"] == 5  # 一半是重复的
        assert stats["unique_count"] == 5
        assert stats["duplicate_rate"] == 0.5