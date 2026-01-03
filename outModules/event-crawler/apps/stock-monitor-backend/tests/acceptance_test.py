#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收测试套件
包含：
1. 数据库连接测试
2. 服务API测试
3. 核心策略逻辑测试
4. 问财数据集成测试
"""

import asyncio
import pytest
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.strategy_service import strategy_service
from app.services.notification_service import notification_service
from app.services.monitor_engine import StockMonitorEngine
from app.models.stock import StockData, MonitorList

# ===========================
# 1. 核心策略测试 (Strategy)
# ===========================

@pytest.mark.asyncio
async def test_strategy_trigger_condition():
    """测试策略触发条件：量比 > 3 且 涨幅 > 3%"""
    
    # 模拟数据：满足条件
    data_success = {
        'code': '600000',
        'current_price': 10.5,
        'volume': 50000,
        'change_percent': 4.5, # > 3%
        'volume_ratio': 3.5,   # > 3.0
        'turnover': 525000
    }
    
    # Mock 通知服务
    with patch.object(notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
        strategy_service.triggered_alerts = {} # 清空历史
        await strategy_service.analyze_tick('600000', data_success)
        
        # 验证是否调用了发送告警
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert '600000' in call_args['title']
        assert 'warning' == call_args['level']

@pytest.mark.asyncio
async def test_strategy_no_trigger_low_volume():
    """测试策略不触发：量比不足"""
    data_fail = {
        'code': '600000',
        'current_price': 10.5,
        'volume': 10000,
        'change_percent': 5.0, 
        'volume_ratio': 1.5,   # < 3.0
        'turnover': 105000
    }
    
    with patch.object(notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
        strategy_service.triggered_alerts = {}
        await strategy_service.analyze_tick('600000', data_fail)
        mock_send.assert_not_called()

@pytest.mark.asyncio
async def test_strategy_cooldown():
    """测试告警冷却机制"""
    data = {
        'code': '600000',
        'current_price': 10.5,
        'volume': 50000,
        'change_percent': 4.5,
        'volume_ratio': 3.5
    }
    
    with patch.object(notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
        strategy_service.triggered_alerts = {}
        
        # 第一次触发
        await strategy_service.analyze_tick('600000', data)
        mock_send.assert_called_once()
        
        mock_send.reset_mock()
        
        # 立即再次触发 (应该被拦截)
        await strategy_service.analyze_tick('600000', data)
        mock_send.assert_not_called()

# ===========================
# 2. 数据模型测试 (Model)
# ===========================

def test_stock_data_model():
    """测试StockData模型字段映射"""
    stock_data = StockData(
        code="000001",
        price=Decimal("10.50"),
        change_percent=Decimal("1.23"),
        volume=1000,
        timestamp=date.today()
    )
    
    assert stock_data.code == "000001"
    assert stock_data.price == Decimal("10.50")

# ===========================
# 3. 监控引擎测试 (Integration)
# ===========================

@pytest.mark.asyncio
async def test_monitor_engine_integration():
    """测试监控引擎集成流程"""
    # Mock MCP Client
    mock_client = AsyncMock()
    mock_client.get_stock_realtime_data.return_value = {
        'success': True,
        'stock_data': [{
            'code': '000001',
            'current_price': 10.0,
            'change_percent': 5.0,
            'volume': 10000,
            'turnover': 100000,
            'volume_ratio': 4.0
        }]
    }
    
    # Mock Session
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    
    # Mock Repo
    with patch('app.services.monitor_engine.MonitorRepository') as MockMonitorRepo, \
         patch('app.services.monitor_engine.StockDataRepository') as MockStockRepo:
        
        # 配置 MonitorRepo 返回活跃股票
        mock_monitor_repo = MockMonitorRepo.return_value
        mock_monitor = MagicMock()
        mock_monitor.code = '000001'
        mock_monitor_repo.find_active_monitors = AsyncMock(return_value=[mock_monitor])

        # 初始化引擎
        engine = StockMonitorEngine(mcp_client=mock_client)
        
        # 运行一次循环
        await engine._process_cycle(mock_session)
        
        # 验证是否调用了 MCP 获取数据
        mock_client.get_stock_realtime_data.assert_called_with(['000001'])
        
        # 验证是否保存了数据
        mock_stock_repo = MockStockRepo.return_value
        mock_stock_repo.create.assert_called_once()
        created_data = mock_stock_repo.create.call_args[0][0]
        assert created_data['code'] == '000001'
        assert created_data['price'] == 10.0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
