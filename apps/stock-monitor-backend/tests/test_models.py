#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型测试
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models.stock import StockInfo, StockData, MonitorList, DataDedupLog, SystemConfig


class TestStockInfo:
    """股票信息模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_stock_info(self, test_session, sample_stock_info):
        """测试创建股票信息"""
        stock = StockInfo(**sample_stock_info)
        test_session.add(stock)
        await test_session.commit()
        
        # 验证创建成功
        result = await test_session.execute(
            select(StockInfo).where(StockInfo.code == "000001")
        )
        saved_stock = result.scalar_one()
        
        assert saved_stock.code == "000001"
        assert saved_stock.name == "平安银行"
        assert saved_stock.market == "SZ"
        assert saved_stock.is_active is True
        assert saved_stock.created_at is not None
        assert saved_stock.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_stock_info_to_dict(self, test_session, sample_stock_info):
        """测试股票信息转字典"""
        stock = StockInfo(**sample_stock_info)
        test_session.add(stock)
        await test_session.commit()
        
        stock_dict = stock.to_dict()
        
        assert stock_dict["code"] == "000001"
        assert stock_dict["name"] == "平安银行"
        assert "created_at" in stock_dict
        assert "updated_at" in stock_dict
    
    @pytest.mark.asyncio
    async def test_stock_info_update_from_dict(self, test_session, sample_stock_info):
        """测试从字典更新股票信息"""
        stock = StockInfo(**sample_stock_info)
        test_session.add(stock)
        await test_session.commit()
        
        # 更新数据
        update_data = {
            "name": "平安银行更新",
            "market": "SH"
        }
        stock.update_from_dict(update_data)
        await test_session.commit()
        
        # 验证更新
        result = await test_session.execute(
            select(StockInfo).where(StockInfo.code == "000001")
        )
        updated_stock = result.scalar_one()
        
        assert updated_stock.name == "平安银行更新"
        assert updated_stock.market == "SH"
        assert updated_stock.is_active is True  # 未更新的字段保持不变


class TestStockData:
    """股票数据模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_stock_data(self, test_session, sample_stock_data):
        """测试创建股票数据"""
        stock_data = StockData(**sample_stock_data)
        test_session.add(stock_data)
        await test_session.commit()
        
        # 验证创建成功
        result = await test_session.execute(
            select(StockData).where(StockData.code == "000001")
        )
        saved_data = result.scalar_one()
        
        assert saved_data.code == "000001"
        assert saved_data.price == 12.50
        assert saved_data.volume == 1000000
        assert saved_data.change_percent == 1.63
        assert saved_data.created_at is not None
    
    @pytest.mark.asyncio
    async def test_stock_data_relationships(self, test_session, sample_stock_info, sample_stock_data):
        """测试股票数据关系"""
        # 创建股票信息
        stock_info = StockInfo(**sample_stock_info)
        test_session.add(stock_info)
        await test_session.commit()
        
        # 创建股票数据
        stock_data = StockData(**sample_stock_data)
        test_session.add(stock_data)
        await test_session.commit()
        
        # 验证关系
        result = await test_session.execute(
            select(StockData).where(StockData.code == "000001")
        )
        saved_data = result.scalar_one()
        
        # 注意：在这个简化的测试中，我们没有设置外键关系
        # 在实际应用中，可以通过关系属性访问相关的股票信息
        assert saved_data.code == stock_info.code


class TestMonitorList:
    """监控列表模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_monitor(self, test_session, sample_monitor):
        """测试创建监控"""
        monitor = MonitorList(**sample_monitor)
        test_session.add(monitor)
        await test_session.commit()
        
        # 验证创建成功
        result = await test_session.execute(
            select(MonitorList).where(MonitorList.code == "000001")
        )
        saved_monitor = result.scalar_one()
        
        assert saved_monitor.code == "000001"
        assert saved_monitor.priority == 5
        assert saved_monitor.is_active is True
        assert saved_monitor.created_at is not None
    
    @pytest.mark.asyncio
    async def test_monitor_unique_constraint(self, test_session, sample_monitor):
        """测试监控唯一约束"""
        # 创建第一个监控
        monitor1 = MonitorList(**sample_monitor)
        test_session.add(monitor1)
        await test_session.commit()
        
        # 尝试创建相同股票代码的监控
        monitor2 = MonitorList(**sample_monitor)
        test_session.add(monitor2)
        
        # 应该抛出异常
        with pytest.raises(Exception):
            await test_session.commit()


class TestDataDedupLog:
    """数据去重日志模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_dedup_log(self, test_session):
        """测试创建去重日志"""
        dedup_log = DataDedupLog(
            table_name="stock_data",
            data_hash="test_hash_123",
            hash_fields="code,timestamp",
            original_data={"code": "000001", "price": 12.50}
        )
        test_session.add(dedup_log)
        await test_session.commit()
        
        # 验证创建成功
        result = await test_session.execute(
            select(DataDedupLog).where(DataDedupLog.data_hash == "test_hash_123")
        )
        saved_log = result.scalar_one()
        
        assert saved_log.data_hash == "test_hash_123"
        assert saved_log.table_name == "stock_data"
        assert saved_log.hash_fields == "code,timestamp"
        assert saved_log.original_data == {"code": "000001", "price": 12.50}
        assert saved_log.created_at is not None
    
    @pytest.mark.asyncio
    async def test_dedup_log_hash_index(self, test_session):
        """测试去重日志哈希索引"""
        # 创建多个去重日志
        logs = [
            DataDedupLog(
                table_name="stock_data",
                data_hash=f"hash_{i}",
                hash_fields="code,timestamp",
                original_data={"code": f"00000{i}", "price": 12.50}
            )
            for i in range(5)
        ]
        
        for log in logs:
            test_session.add(log)
        await test_session.commit()
        
        # 通过哈希查询
        result = await test_session.execute(
            select(DataDedupLog).where(DataDedupLog.data_hash == "hash_2")
        )
        found_log = result.scalar_one()
        
        assert found_log.data_hash == "hash_2"


class TestSystemConfig:
    """系统配置模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_system_config(self, test_session):
        """测试创建系统配置"""
        config = SystemConfig(
            config_key="test_key",
            config_value="test_value",
            description="测试配置"
        )
        test_session.add(config)
        await test_session.commit()
        
        # 验证创建成功
        result = await test_session.execute(
            select(SystemConfig).where(SystemConfig.config_key == "test_key")
        )
        saved_config = result.scalar_one()
        
        assert saved_config.config_key == "test_key"
        assert saved_config.config_value == "test_value"
        assert saved_config.description == "测试配置"
        assert saved_config.created_at is not None
    
    @pytest.mark.asyncio
    async def test_system_config_unique_key(self, test_session):
        """测试系统配置键唯一性"""
        # 创建第一个配置
        config1 = SystemConfig(
            config_key="duplicate_key",
            config_value="value1"
        )
        test_session.add(config1)
        await test_session.commit()
        
        # 尝试创建相同键的配置
        config2 = SystemConfig(
            config_key="duplicate_key",
            config_value="value2"
        )
        test_session.add(config2)
        
        # 应该抛出异常
        with pytest.raises(Exception):
            await test_session.commit()


class TestTimestampMixin:
    """时间戳混入测试"""
    
    @pytest.mark.asyncio
    async def test_timestamp_auto_creation(self, test_session, sample_stock_info):
        """测试时间戳自动创建"""
        stock = StockInfo(**sample_stock_info)
        test_session.add(stock)
        await test_session.commit()
        
        assert stock.created_at is not None
        assert stock.updated_at is not None
        assert stock.created_at == stock.updated_at
    
    @pytest.mark.asyncio
    async def test_timestamp_auto_update(self, test_session, sample_stock_info):
        """测试时间戳自动更新"""
        stock = StockInfo(**sample_stock_info)
        test_session.add(stock)
        await test_session.commit()
        
        original_updated_at = stock.updated_at
        
        # 等待一小段时间确保时间戳不同
        import asyncio
        await asyncio.sleep(0.01)
        
        # 更新记录
        stock.name = "更新后的名称"
        await test_session.commit()
        
        # 验证updated_at已更新
        assert stock.updated_at > original_updated_at
        assert stock.created_at < stock.updated_at