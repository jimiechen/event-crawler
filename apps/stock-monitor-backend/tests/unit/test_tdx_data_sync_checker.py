#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘后数据同步检查器单元测试
TDD Step 1: 编写测试用例 (红)
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

# 被测试的类 (先定义接口，稍后实现)
from app.services.tdx_data_sync_checker import TdxDataSyncChecker


class TestTdxClientConnection:
    """测试通达信客户端连接检查"""
    
    def test_client_online(self):
        """
        测试场景: 通达信客户端在线
        预期结果: 返回 online=True
        """
        # Arrange
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        
        # Act
        result = checker.check_client_connection()
        
        # Assert
        assert result["online"] is True
        assert result["status"] == "success"
    
    def test_client_offline(self):
        """
        测试场景: 通达信客户端离线
        预期结果: 返回 online=False, 触发告警
        """
        # Arrange
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = False
        checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        
        # Act
        result = checker.check_client_connection()
        
        # Assert
        assert result["online"] is False
        assert result["status"] == "failed"
        assert result["action_required"] is True
    
    def test_client_timeout(self):
        """
        测试场景: 通达信客户端连接超时
        预期结果: 返回 timeout 错误
        """
        # Arrange
        mock_tdx = Mock()
        mock_tdx.is_connected.side_effect = TimeoutError("Connection timeout")
        checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        
        # Act
        result = checker.check_client_connection()
        
        # Assert
        assert result["status"] == "timeout"
        assert "timeout" in result["error_message"].lower()


class TestDataCompleteness:
    """测试数据完整性检查"""
    
    def test_data_complete(self):
        """
        测试场景: 当日数据完整
        预期结果: data_complete=True
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_data = self._generate_complete_data(trade_date, stock_count=5000)
        mock_tdx = Mock()
        mock_tdx.get_market_data.return_value = mock_data
        checker = TdxDataSyncChecker(tdx_client=mock_tdx, expected_stock_count=5000)
        
        # Act
        result = checker.check_data_completeness(trade_date)
        
        # Assert
        assert result["data_complete"] is True
        assert result["missing_stocks"] == []
    
    def test_data_incomplete(self):
        """
        测试场景: 部分股票数据缺失
        预期结果: data_complete=False, 列出缺失股票
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        # 缺失30条，剩余70条，小于100*0.8=80，应该判定为不完整
        mock_data = self._generate_incomplete_data(trade_date, total_count=100, missing_count=30)
        mock_tdx = Mock()
        mock_tdx.get_market_data.return_value = mock_data
        checker = TdxDataSyncChecker(tdx_client=mock_tdx, expected_stock_count=100)
        
        # Act
        result = checker.check_data_completeness(trade_date)
        
        # Assert
        assert result["data_complete"] is False
        assert len(result["missing_stocks"]) == 30
    
    def test_empty_data(self):
        """
        测试场景: 数据完全为空
        预期结果: data_complete=False, 严重错误
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_tdx = Mock()
        mock_tdx.get_market_data.return_value = []
        checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        
        # Act
        result = checker.check_data_completeness(trade_date)
        
        # Assert
        assert result["data_complete"] is False
        assert result["severity"] == "critical"
    
    def _generate_complete_data(self, trade_date: date, stock_count: int = 100) -> list:
        """生成完整的模拟数据"""
        data = []
        for i in range(stock_count):
            data.append({
                "code": f"{i:06d}.SZ",
                "date": trade_date,
                "open": 10.0 + i * 0.1,
                "close": 11.0 + i * 0.1,
                "high": 11.5 + i * 0.1,
                "low": 9.5 + i * 0.1,
                "volume": 1000000 + i * 10000
            })
        return data
    
    def _generate_incomplete_data(self, trade_date: date, total_count: int = 100, missing_count: int = 5) -> list:
        """生成不完整的模拟数据"""
        data = self._generate_complete_data(trade_date, stock_count=total_count)
        # 模拟缺失部分数据
        return data[:-missing_count]


class TestTimestampValidity:
    """测试时间戳有效性检查"""
    
    @pytest.mark.parametrize("data_date,expected_valid", [
        (date(2026, 3, 25), True),   # 当日数据
        (date(2026, 3, 24), False),  # 昨日数据
        (date(2026, 3, 26), False),  # 未来数据
    ])
    def test_timestamp_check(self, data_date, expected_valid):
        """
        测试场景: 不同日期的数据时间戳
        预期结果: 只有当日数据通过
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_data = self._generate_data_with_date(data_date)
        mock_tdx = Mock()
        mock_tdx.get_market_data.return_value = mock_data
        checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        
        # Act
        result = checker.check_timestamp(trade_date)
        
        # Assert
        assert result["timestamp_valid"] == expected_valid
    
    def _generate_data_with_date(self, data_date: date) -> list:
        """生成指定日期的模拟数据"""
        return [{
            "code": "000001.SZ",
            "date": data_date,
            "open": 10.0,
            "close": 11.0,
            "high": 11.5,
            "low": 9.5,
            "volume": 1000000
        }]


class TestDataReasonableness:
    """测试数据合理性检查"""
    
    def test_reasonable_prices(self):
        """
        测试场景: 价格在合理范围内
        预期结果: data_reasonable=True
        """
        # Arrange
        mock_data = {
            "open": 10.5,
            "close": 11.2,
            "high": 11.5,
            "low": 10.2,
            "volume": 1000000
        }
        checker = TdxDataSyncChecker()
        
        # Act
        result = checker.check_data_reasonableness(mock_data)
        
        # Assert
        assert result["data_reasonable"] is True
    
    def test_unreasonable_price_zero(self):
        """
        测试场景: 价格为0
        预期结果: data_reasonable=False
        """
        # Arrange
        mock_data = {
            "open": 0,
            "close": 11.2,
            "high": 11.5,
            "low": 10.2,
            "volume": 1000000
        }
        checker = TdxDataSyncChecker()
        
        # Act
        result = checker.check_data_reasonableness(mock_data)
        
        # Assert
        assert result["data_reasonable"] is False
        assert any("zero price" in issue for issue in result["issues"])
    
    def test_unreasonable_volume_negative(self):
        """
        测试场景: 成交量为负数
        预期结果: data_reasonable=False
        """
        # Arrange
        mock_data = {
            "open": 10.5,
            "close": 11.2,
            "high": 11.5,
            "low": 10.2,
            "volume": -100
        }
        checker = TdxDataSyncChecker()
        
        # Act
        result = checker.check_data_reasonableness(mock_data)
        
        # Assert
        assert result["data_reasonable"] is False
        assert "negative volume" in result["issues"]
    
    def test_high_low_inversion(self):
        """
        测试场景: 最低价 > 最高价
        预期结果: data_reasonable=False
        """
        # Arrange
        mock_data = {
            "open": 10.5,
            "close": 11.2,
            "high": 10.0,  # 错误: 最高价比最低价还低
            "low": 11.0,
            "volume": 1000000
        }
        checker = TdxDataSyncChecker()
        
        # Act
        result = checker.check_data_reasonableness(mock_data)
        
        # Assert
        assert result["data_reasonable"] is False
        assert "high < low" in result["issues"]


class TestDailyDataSyncCheck:
    """测试完整的盘后数据同步检查"""
    
    def test_all_checks_pass(self):
        """
        测试场景: 所有检查都通过
        预期结果: 返回 success 状态
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        # 生成5000条数据以满足完整性检查
        mock_data = []
        for i in range(5000):
            mock_data.append({
                "code": f"{i:06d}.SZ",
                "date": trade_date,
                "open": 10.5,
                "close": 11.2,
                "high": 11.5,
                "low": 10.2,
                "volume": 1000000
            })
        mock_tdx.get_market_data.return_value = mock_data
        
        checker = TdxDataSyncChecker(tdx_client=mock_tdx, expected_stock_count=5000)
        
        # Act
        result = checker.check_daily_data_sync(trade_date)
        
        # Assert
        assert result["status"] == "success"
        assert result["checks"]["client_online"] is True
        assert result["checks"]["data_complete"] is True
        assert result["checks"]["timestamp_valid"] is True
        assert result["checks"]["data_reasonable"] is True
        assert result["action_required"] is False
    
    def test_client_offline_failure(self):
        """
        测试场景: 客户端离线
        预期结果: 返回 failed 状态，需要操作员介入
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = False
        
        checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        
        # Act
        result = checker.check_daily_data_sync(trade_date)
        
        # Assert
        assert result["status"] == "failed"
        assert result["checks"]["client_online"] is False
        assert result["action_required"] is True
        assert "客户端离线" in result["message"]
    
    def test_data_incomplete_failure(self):
        """
        测试场景: 数据不完整
        预期结果: 返回 failed 状态
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = []  # 空数据
        
        checker = TdxDataSyncChecker(tdx_client=mock_tdx)
        
        # Act
        result = checker.check_daily_data_sync(trade_date)
        
        # Assert
        assert result["status"] == "failed"
        assert result["checks"]["data_complete"] is False
        assert result["action_required"] is True
    
    def _generate_valid_data(self, trade_date: date) -> list:
        """生成有效的模拟数据"""
        return [{
            "code": "000001.SZ",
            "date": trade_date,
            "open": 10.5,
            "close": 11.2,
            "high": 11.5,
            "low": 10.2,
            "volume": 1000000
        }]


class TestNotificationTrigger:
    """测试通知触发逻辑"""
    
    @pytest.mark.asyncio
    async def test_should_notify_on_failure(self):
        """
        测试场景: 检查失败时应该触发通知
        预期结果: 返回 should_notify=True
        """
        # Arrange
        checker = TdxDataSyncChecker()
        failed_result = {
            "status": "failed",
            "action_required": True
        }
        
        # Act
        should_notify = checker.should_notify_operator(failed_result)
        
        # Assert
        assert should_notify is True
    
    @pytest.mark.asyncio
    async def test_should_not_notify_on_success(self):
        """
        测试场景: 检查成功时不应该触发通知
        预期结果: 返回 should_notify=False
        """
        # Arrange
        checker = TdxDataSyncChecker()
        success_result = {
            "status": "success",
            "action_required": False
        }
        
        # Act
        should_notify = checker.should_notify_operator(success_result)
        
        # Assert
        assert should_notify is False
