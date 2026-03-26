#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日板块创建与选股单元测试
TDD Step 1: 编写测试用例 (红)
"""

import pytest
import pandas as pd
from datetime import date
from unittest.mock import Mock, patch
from typing import List, Dict, Any

# 被测试的类 (先定义接口，稍后实现)
from app.services.daily_stock_selection_service import DailyStockSelectionService
from app.services.stock_selector import StockSelector


class TestSectorNaming:
    """测试板块命名规则"""
    
    @pytest.mark.parametrize("trade_date,expected_code,expected_name", [
        (date(2026, 3, 25), "3BL0325", "3倍量20260325"),
        (date(2026, 12, 31), "3BL1231", "3倍量20261231"),
        (date(2026, 1, 1), "3BL0101", "3倍量20260101"),
    ])
    def test_sector_naming(self, trade_date, expected_code, expected_name):
        """
        测试场景: 不同日期的板块命名
        预期结果: 代码和名称符合规范
        """
        # Arrange
        service = DailyStockSelectionService()
        
        # Act
        sector_code, sector_name = service.generate_sector_names(trade_date)
        
        # Assert
        assert sector_code == expected_code
        assert sector_name == expected_name


class TestThreeTimesVolumeSelection:
    """测试三倍量选股算法"""
    
    def test_select_3x_volume_stocks(self):
        """
        测试场景: 筛选三倍量股票
        预期结果: 只返回成交量 >= 前日3倍的股票
        """
        # Arrange
        volume_data = pd.DataFrame({
            "000001.SZ": [1000, 3500],  # 3.5倍 - 选中
            "000002.SZ": [1000, 2500],  # 2.5倍 - 不选
            "600000.SH": [1000, 3000],  # 3倍 - 选中
            "600001.SH": [1000, 5000],  # 5倍 - 选中
        }, index=["prev_volume", "volume"])
        
        selector = StockSelector()
        
        # Act
        selected = selector.select_3x_volume(volume_data)
        
        # Assert
        assert "000001.SZ" in selected
        assert "000002.SZ" not in selected
        assert "600000.SH" in selected
        assert "600001.SH" in selected
        assert len(selected) == 3
    
    def test_exclude_zero_volume(self):
        """
        测试场景: 排除成交量为0的股票
        预期结果: 不选中成交量为0的股票
        """
        # Arrange
        volume_data = pd.DataFrame({
            "000001.SZ": [0, 0],        # 前日0，当日0 - 不选
            "000002.SZ": [1000, 0],     # 当日0 - 不选
            "600000.SH": [1000, 3000],  # 正常 - 选中
        }, index=["prev_volume", "volume"])
        
        selector = StockSelector()
        
        # Act
        selected = selector.select_3x_volume(volume_data)
        
        # Assert
        assert len(selected) == 1
        assert "600000.SH" in selected
    
    def test_exclude_negative_volume(self):
        """
        测试场景: 排除成交量为负数的股票
        预期结果: 不选中成交量为负数的股票
        """
        # Arrange
        volume_data = pd.DataFrame({
            "000001.SZ": [1000, -100],  # 负数 - 不选
            "600000.SH": [1000, 3000],  # 正常 - 选中
        }, index=["prev_volume", "volume"])
        
        selector = StockSelector()
        
        # Act
        selected = selector.select_3x_volume(volume_data)
        
        # Assert
        assert len(selected) == 1
        assert "600000.SH" in selected


class TestLimitUpSelection:
    """测试涨停选股算法"""
    
    @pytest.mark.parametrize("market,change_pct,expected_selected", [
        ("SH", 9.8, True),   # 主板涨停
        ("SH", 9.7, False),  # 主板未涨停
        ("SZ", 9.8, True),   # 深市主板涨停
        ("SZ", 9.7, False),  # 深市主板未涨停
        ("CY", 19.8, True),  # 创业板涨停
        ("CY", 19.7, False), # 创业板未涨停
        ("KC", 19.8, True),  # 科创板涨停
        ("KC", 19.7, False), # 科创板未涨停
        ("BJ", 29.8, True),  # 北交所涨停
        ("BJ", 29.7, False), # 北交所未涨停
    ])
    def test_limit_up_by_market(self, market, change_pct, expected_selected):
        """
        测试场景: 不同市场的涨停判断
        预期结果: 根据市场类型正确判断涨停
        """
        # Arrange
        stock_data = {
            "code": "000001.SZ",
            "market": market,
            "change_percent": change_pct
        }
        selector = StockSelector()
        
        # Act
        is_limit_up = selector.check_limit_up(stock_data)
        
        # Assert
        assert is_limit_up == expected_selected
    
    def test_limit_up_thresholds(self):
        """
        测试场景: 验证各市场涨停阈值
        预期结果: 主板9.8%，创业板/科创板19.8%，北交所29.8%
        """
        # Arrange
        selector = StockSelector()
        
        # Assert - 主板
        assert selector.get_limit_up_threshold("SH") == 9.8
        assert selector.get_limit_up_threshold("SZ") == 9.8
        
        # Assert - 创业板/科创板
        assert selector.get_limit_up_threshold("CY") == 19.8
        assert selector.get_limit_up_threshold("KC") == 19.8
        
        # Assert - 北交所
        assert selector.get_limit_up_threshold("BJ") == 29.8


class TestGapSelection:
    """测试缺口选股算法"""
    
    def test_upward_gap(self):
        """
        测试场景: 向上缺口
        预期结果: 当日最低价 > 前日最高价时选中
        """
        # Arrange
        price_data = {
            "prev_high": 10.0,
            "today_low": 10.5  # 向上缺口0.5元
        }
        selector = StockSelector()
        
        # Act
        has_gap = selector.check_upward_gap(price_data)
        
        # Assert
        assert has_gap is True
    
    def test_no_gap(self):
        """
        测试场景: 无缺口
        预期结果: 当日最低价 <= 前日最高价时不选中
        """
        # Arrange
        price_data = {
            "prev_high": 10.0,
            "today_low": 9.8  # 无缺口
        }
        selector = StockSelector()
        
        # Act
        has_gap = selector.check_upward_gap(price_data)
        
        # Assert
        assert has_gap is False
    
    def test_downward_gap(self):
        """
        测试场景: 向下缺口（不选中）
        预期结果: 向下缺口不选中（我们只关心向上缺口）
        """
        # Arrange
        price_data = {
            "prev_high": 10.0,
            "today_low": 9.0  # 向下缺口
        }
        selector = StockSelector()
        
        # Act
        has_gap = selector.check_upward_gap(price_data)
        
        # Assert
        assert has_gap is False


class TestDailySelectionExecution:
    """测试每日选股执行"""
    
    def _generate_mock_market_data(self, trade_date: date, count: int = 5000):
        """生成模拟市场数据"""
        data = []
        for i in range(count):
            code = f"{i:06d}"
            if i % 2 == 0:
                code += ".SZ"
            else:
                code += ".SH"
            data.append({
                "code": code,
                "date": trade_date,
                "open": 10.0,
                "close": 11.0,
                "high": 11.5,
                "low": 9.5,
                "volume": 1000000
            })
        return data
    
    def test_execute_daily_selection_success(self):
        """
        测试场景: 成功执行每日选股
        预期结果: 创建板块，选股结果写入板块
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        # 模拟市场数据 - 生成足够的数据量
        mock_market_data = self._generate_mock_market_data(trade_date, count=5000)
        mock_tdx.get_market_data.return_value = mock_market_data
        
        service = DailyStockSelectionService(tdx_client=mock_tdx)
        
        # Act
        result = service.execute_daily_selection(trade_date)
        
        # Assert
        assert result["status"] == "success"
        assert result["sector_code"] == "3BL0325"
        assert mock_tdx.create_sector.called
        assert mock_tdx.send_user_block.called
    
    def test_execute_daily_selection_with_data_sync_check(self):
        """
        测试场景: 执行选股前先进行数据同步检查
        预期结果: 数据检查失败时暂停选股
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = False  # 模拟客户端离线
        
        service = DailyStockSelectionService(tdx_client=mock_tdx)
        
        # Act
        result = service.execute_daily_selection(trade_date)
        
        # Assert
        assert result["status"] == "paused"
        assert result["reason"] == "data_sync_failed"
        assert not mock_tdx.create_sector.called
    
    def test_execute_daily_selection_multiple_strategies(self):
        """
        测试场景: 执行多种选股策略
        预期结果: 返回每种策略的选股结果
        """
        # Arrange
        trade_date = date(2026, 3, 25)
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        # 模拟市场数据 - 生成足够的数据量
        mock_market_data = self._generate_mock_market_data(trade_date, count=5000)
        mock_tdx.get_market_data.return_value = mock_market_data
        
        service = DailyStockSelectionService(tdx_client=mock_tdx)
        
        # Act
        result = service.execute_daily_selection(
            trade_date,
            strategies=["3x_volume", "limit_up", "gap"]
        )
        
        # Assert
        assert result["status"] == "success"
        assert "strategies" in result
        assert "3x_volume" in result["strategies"]
        assert "limit_up" in result["strategies"]
        assert "gap" in result["strategies"]


class TestSectorCreation:
    """测试板块创建"""
    
    def test_create_sector_success(self):
        """
        测试场景: 成功创建板块
        预期结果: 返回True
        """
        # Arrange
        mock_tdx = Mock()
        mock_tdx.create_sector.return_value = True
        
        service = DailyStockSelectionService(tdx_client=mock_tdx)
        
        # Act
        result = service.create_sector("3BL0325", "3倍量20260325")
        
        # Assert
        assert result is True
        mock_tdx.create_sector.assert_called_once_with(
            block_code="3BL0325",
            block_name="3倍量20260325"
        )
    
    def test_create_sector_failure(self):
        """
        测试场景: 创建板块失败
        预期结果: 返回False，记录错误
        """
        # Arrange
        mock_tdx = Mock()
        mock_tdx.create_sector.return_value = False
        
        service = DailyStockSelectionService(tdx_client=mock_tdx)
        
        # Act
        result = service.create_sector("3BL0325", "3倍量20260325")
        
        # Assert
        assert result is False
    
    def test_send_stocks_to_sector(self):
        """
        测试场景: 将股票发送到板块
        预期结果: 股票列表成功写入板块
        """
        # Arrange
        mock_tdx = Mock()
        mock_tdx.send_user_block.return_value = True
        
        service = DailyStockSelectionService(tdx_client=mock_tdx)
        stocks = ["000001.SZ", "600000.SH", "000002.SZ"]
        
        # Act
        result = service.send_stocks_to_sector("3BL0325", stocks)
        
        # Assert
        assert result is True
        mock_tdx.send_user_block.assert_called_once_with(
            block_code="3BL0325",
            stocks=stocks
        )


class TestStockExclusionRules:
    """测试股票排除规则"""
    
    def test_exclude_st_stocks(self):
        """
        测试场景: 排除ST股票
        预期结果: ST股票不被选中
        """
        # Arrange
        selector = StockSelector()
        
        stock_data = {
            "code": "000001.SZ",
            "name": "*ST股票",
            "change_percent": 9.8
        }
        
        # Act
        should_exclude = selector.should_exclude_stock(stock_data)
        
        # Assert
        assert should_exclude is True
    
    def test_exclude_new_stocks(self):
        """
        测试场景: 排除新股（上市<20天）
        预期结果: 新股不被选中
        """
        # Arrange
        selector = StockSelector()
        
        stock_data = {
            "code": "000001.SZ",
            "list_date": date(2026, 3, 20),  # 刚上市5天
            "change_percent": 9.8
        }
        
        # Act - 假设今天是2026-03-25
        should_exclude = selector.should_exclude_stock(stock_data, reference_date=date(2026, 3, 25))
        
        # Assert
        assert should_exclude is True
    
    def test_exclude_suspended_stocks(self):
        """
        测试场景: 排除停牌股票
        预期结果: 停牌股票不被选中
        """
        # Arrange
        selector = StockSelector()
        
        stock_data = {
            "code": "000001.SZ",
            "is_suspended": True,
            "change_percent": 0
        }
        
        # Act
        should_exclude = selector.should_exclude_stock(stock_data)
        
        # Assert
        assert should_exclude is True
