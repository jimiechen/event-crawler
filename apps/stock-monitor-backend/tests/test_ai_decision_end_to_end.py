import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from app.services.ai_decision_service import AIDecisionService, AIDecisionConfig
from app.models.stock import StockData
# from app.config.settings import DeepSeekConfig

# Sample Data
STOCK_CODE = "000001"
TEMPLATE_WITH_INDICATORS = """
Stock: {stock_code}
MA5: {000001_MA_5}
MACD: {000001_MACD_default}
"""

@pytest.mark.asyncio
async def test_generate_decision_end_to_end():
    # 1. Setup Mock Session
    mock_session = AsyncMock()
    
    # 2. Setup Mock Repositories
    with patch("app.services.ai_decision_service.StockRepository") as MockStockRepo, \
         patch("app.services.ai_decision_service.StockDataRepository") as MockDataRepo, \
         patch("httpx.AsyncClient") as MockClient:
        
        # Configure StockRepository Mock
        mock_stock_repo = MockStockRepo.return_value
        mock_stock_repo.find_by_code = AsyncMock(return_value=MagicMock(code=STOCK_CODE, name="平安银行"))
        
        # Configure StockDataRepository Mock (Return 30 days of data)
        mock_data_repo = MockDataRepo.return_value
        data = []
        start_date = datetime(2023, 1, 1)
        for i in range(30):
            date = start_date + timedelta(days=i)
            price = 10.0 + i
            data.append(StockData(
                code=STOCK_CODE,
                timestamp=date,
                open_price=price - 0.5,
                high_price=price + 0.5,
                low_price=price - 0.5,
                price=price, # Close
                volume=1000 + i * 100,
                request_timestamp=date
            ))
        
        # Mock find_by_code (returns list)
        mock_data_repo.find_by_code = AsyncMock(return_value=data)
        
        # Mock find_latest_by_code (returns single item)
        mock_data_repo.find_latest_by_code = AsyncMock(return_value=data[-1])
        
        # Mock get_history (if called)
        mock_data_repo.get_history = AsyncMock(return_value=data)
        
        # Configure LLM Mock
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": """
                    {
                        "decisions": [
                            {
                                "operation": "buy",
                                "stock_code": "000001",
                                "stock_name": "平安银行",
                                "target_portion_of_balance": 0.5,
                                "max_price": 40.0,
                                "reason": "MA5 is rising",
                                "trading_strategy": "Hold"
                            }
                        ]
                    }
                    """
                }
            }]
        }
        mock_client_instance.post.return_value = mock_response
        
        # 3. Instantiate Service
        config = AIDecisionConfig(api_key="test", base_url="http://test", model="test-model")
        service = AIDecisionService(config)
        
        # 4. Run generate_decision
        decision = await service.generate_decision(
            session=mock_session,
            stock_code=STOCK_CODE,
            template_text=TEMPLATE_WITH_INDICATORS
        )
        
        # 5. Verify Results
        assert decision["stock_code"] == STOCK_CODE
        assert "decisions" in decision
        assert decision["decisions"][0]["operation"] == "buy"
        
        # 6. Verify Context Building (Implicitly checked by template formatting)
        # Check if LLM was called with formatted prompt containing indicator values
        call_args = mock_client_instance.post.call_args
        assert call_args is not None
        payload = call_args[1]["json"]
        prompt_sent = payload["messages"][1]["content"]
        
        print(f"Prompt Sent: {prompt_sent}")
        
        # Verify indicators were replaced
        # MA5 of last 5 days: prices are 39.0, 38.0, 37.0, 36.0, 35.0 (indices 29, 28, 27, 26, 25)
        # Wait, data generation:
        # price = 10.0 + i
        # i=29: price=39.0
        # i=28: price=38.0
        # ...
        # Avg(39, 38, 37, 36, 35) = 37.0
        assert "MA5: 37.0" in prompt_sent or "MA5: 37.00" in prompt_sent
        assert "MACD:" in prompt_sent
        assert "DIF" in prompt_sent # MACD string format contains DIF
