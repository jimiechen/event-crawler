#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化监控流程测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime

from app.services.monitor_engine import StockMonitorEngine
from app.services.strategy_service import strategy_service
from app.services.notification_service import notification_service
from app.repositories.monitor_repository import MonitorRepository
from app.repositories.stock_repository import StockDataRepository

@pytest.mark.asyncio
async def test_monitor_engine_flow(test_session):
    """测试监控引擎流程"""
    
    # 1. 准备数据：在数据库中添加监控股票
    monitor_repo = MonitorRepository(test_session)
    await monitor_repo.add_monitor("000001", priority=10)
    await test_session.commit()
    
    # 重置策略服务的告警状态，防止其他测试干扰
    strategy_service.triggered_alerts = {}
    
    # 2. Mock MCP Client
    mock_client = AsyncMock()
    mock_client.get_stock_realtime_data.return_value = {
        'success': True,
        'stock_data': [
            {
                'code': '000001',
                'current_price': 10.0,
                'volume': 10000,
                'change_percent': 5.0, # 涨幅 > 3%
                'turnover': 100000,
                'volume_ratio': 4.0 # 量比 > 3
            }
        ]
    }
    
    # 3. Mock Strategy Service 和 Notification Service
    # 我们想测试 strategy_service 是否真正调用了 notification
    # 所以我们只 mock notification_service.send_alert
    
    with patch.object(notification_service, 'send_alert', new_callable=AsyncMock) as mock_send_alert:
        
        # 4. 初始化引擎
        engine = StockMonitorEngine(mcp_client=mock_client)
        
        # 5. 运行一次循环 (手动调用 _process_cycle)
        await engine._process_cycle(test_session)
        
        # 6. 验证是否保存了数据
        stock_repo = StockDataRepository(test_session)
        saved_data = await stock_repo.find_by_code("000001")
        assert len(saved_data) > 0
        assert float(saved_data[0].price) == 10.0
        
        # 7. 验证是否触发告警
        # 策略：量比(4.0) > 3.0 且 涨幅(5.0) > 3.0 -> 应该触发
        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args
        assert "股价异动提醒: 000001" in call_args[1]['title']
        assert "量比(4.0) > 3.0" in call_args[1]['data']['reason']

@pytest.mark.asyncio
async def test_strategy_logic():
    """测试策略逻辑"""
    
    # Case 1: 不满足条件 (量比低)
    data_normal = {
        'code': '000001', 'current_price': 10.0, 'volume': 1000,
        'change_percent': 5.0, 'volume_ratio': 1.0
    }
    
    with patch.object(notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
        # 重置触发记录
        strategy_service.triggered_alerts = {}
        
        await strategy_service.analyze_tick('000001', data_normal)
        mock_send.assert_not_called()
        
    # Case 2: 不满足条件 (涨幅低)
    data_flat = {
        'code': '000001', 'current_price': 10.0, 'volume': 10000,
        'change_percent': 1.0, 'volume_ratio': 4.0
    }
    
    with patch.object(notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
        strategy_service.triggered_alerts = {}
        await strategy_service.analyze_tick('000001', data_flat)
        mock_send.assert_not_called()
        
    # Case 3: 满足条件
    data_trigger = {
        'code': '000001', 'current_price': 10.0, 'volume': 10000,
        'change_percent': 4.0, 'volume_ratio': 4.0
    }
    
    with patch.object(notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
        strategy_service.triggered_alerts = {}
        await strategy_service.analyze_tick('000001', data_trigger)
        mock_send.assert_called_once()
