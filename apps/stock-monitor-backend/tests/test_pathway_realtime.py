import pytest
from unittest.mock import AsyncMock, patch
from app.services.pathway_engine import PathwayVolumePriceEngine

@pytest.mark.asyncio
async def test_process_realtime_batch_alerts():
    """测试实时批处理 - 触发告警"""
    # Setup
    mock_session = AsyncMock()
    engine = PathwayVolumePriceEngine(mock_session)
    
    # Mock sse_service to capture broadcast calls
    with patch('app.services.pathway_engine.sse_service') as mock_sse:
        mock_sse.broadcast = AsyncMock()
        
        # Test Data: One triggers alert (Change > 5%), one doesn't
        data_list = [
            {
                'stock_code': '000001', 'stock_name': 'Test1', 
                'current_price': 10.0, 'change_percent': 6.0, # Trigger > 5%
                'volume': 100, 'turnover': 1.0, 'request_timestamp': 123456
            },
            {
                'stock_code': '000002', 'stock_name': 'Test2', 
                'current_price': 20.0, 'change_percent': 1.0, 
                'volume': 100, 'turnover': 1.0, 'request_timestamp': 123456
            }
        ]
        
        # Action
        await engine.process_realtime_batch(data_list)
        
        # Assert
        assert mock_sse.broadcast.call_count == 1
        call_args = mock_sse.broadcast.call_args
        assert call_args[0][0] == "alert"
        payload = call_args[0][1]
        assert payload['symbol'] == '000001'
        assert "大幅上涨" in payload['message']

@pytest.mark.asyncio
async def test_process_realtime_batch_no_alerts():
    """测试实时批处理 - 无告警"""
    # Setup
    mock_session = AsyncMock()
    engine = PathwayVolumePriceEngine(mock_session)
    
    # Mock sse_service
    with patch('app.services.pathway_engine.sse_service') as mock_sse:
        mock_sse.broadcast = AsyncMock()
        
        data_list = [
            {
                'stock_code': '000003', 'stock_name': 'Test3', 
                'current_price': 10.0, 'change_percent': 1.0, 
                'volume': 100, 'turnover': 1.0, 'request_timestamp': 123456
            }
        ]
        
        # Action
        await engine.process_realtime_batch(data_list)
        
        # Assert
        mock_sse.broadcast.assert_not_called()

@pytest.mark.asyncio
async def test_process_realtime_batch_volume_alert():
    """测试实时批处理 - 量比告警"""
    # Setup
    mock_session = AsyncMock()
    engine = PathwayVolumePriceEngine(mock_session)
    
    # Mock _get_cached_baseline to return baseline data
    # Note: Since we are mocking the method on the instance, we need to make sure it's awaitable
    engine._get_cached_baseline = AsyncMock(return_value={
        'last_vol': 1000.0, # Small baseline volume
        'last_5d_low_vol': 500.0
    })

    # Mock sse_service
    with patch('app.services.pathway_engine.sse_service') as mock_sse:
        mock_sse.broadcast = AsyncMock()
        
        # Test Data: Trigger Volume Ratio > 3.0 (Volume 4000 vs Baseline 1000)
        data_list = [
            {
                'stock_code': '000004', 'stock_name': 'VolTest', 
                'current_price': 10.0, 'change_percent': 1.0, 
                'volume': 4000, 'turnover': 1.0, 'request_timestamp': 123456
            }
        ]
        
        # Action
        await engine.process_realtime_batch(data_list)
        
        # Assert
        assert mock_sse.broadcast.call_count == 1
        payload = mock_sse.broadcast.call_args[0][1]
        assert payload['symbol'] == '000004'
        assert "实时3倍量" in payload['message']

