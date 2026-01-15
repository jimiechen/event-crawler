
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from app.services.ai_decision_service import AIDecisionService, AIDecisionConfig
from app.models.stock import StockData
from app.repositories.stock_repository import StockDataRepository, StockRepository

# Mock StockData
def create_stock_data(date_str, price, open_p, high, low, volume):
    return StockData(
        timestamp=datetime.strptime(date_str, "%Y-%m-%d"),
        price=price,
        open_price=open_p,
        high_price=high,
        low_price=low,
        volume=volume,
        code="000001",
        request_timestamp=datetime.now()
    )

@pytest.mark.asyncio
async def test_indicator_calculation():
    # 1. Setup Data (30 days of data)
    # Simple uptrend: Price increases by 1 each day
    data = []
    start_date = datetime(2023, 1, 1)
    for i in range(30):
        date = start_date + timedelta(days=i)
        price = 10.0 + i
        data.append(create_stock_data(
            date.strftime("%Y-%m-%d"), 
            price, # Close
            price - 0.5, # Open
            price + 0.5, # High
            price - 0.5, # Low
            1000 + i * 100 # Volume
        ))
        
    # 2. Mock Repositories
    mock_session = AsyncMock()
    
    # We need to patch the repository creation inside the service or mock the session interaction
    # AIDecisionService instantiates repositories inside methods using session.
    # So we can't easily inject mock repositories unless we refactor.
    # However, Python mocks can patch classes.
    
    with pytest.MonkeyPatch.context() as m:
        # Mock StockRepository
        mock_stock_repo = AsyncMock()
        mock_stock_repo.find_by_code.return_value = MagicMock(code="000001", name="Test Stock")
        m.setattr("app.services.ai_decision_service.StockRepository", lambda s: mock_stock_repo)
        
        # Mock StockDataRepository
        mock_data_repo = AsyncMock()
        mock_data_repo.find_latest_by_code.return_value = data[-1]
        mock_data_repo.find_by_code.return_value = data
        m.setattr("app.services.ai_decision_service.StockDataRepository", lambda s: mock_data_repo)
        
        # Mock _get_tags
        service = AIDecisionService(AIDecisionConfig(api_key="test", base_url="test", model="test"))
        service._get_tags = AsyncMock(return_value={"tags": []})
        
        # 3. Test Template with Indicators
        template = """
        Analysis for {000001}:
        MA5: {000001_MA_5}
        RSI: {000001_RSI_14}
        MACD: {000001_MACD_default}
        """
        
        context = await service.prepare_decision_context(mock_session, "000001", template)
        
        # 4. Verify Calculations
        # MA5 of last 5 days: (39+38+37+36+35)/5 = 37.0
        # (Price sequence: 10, 11, ..., 39)
        # Last price is 39 (10 + 29)
        
        print("Context Keys:", context.keys())
        print("MA5:", context.get("000001_MA_5"))
        print("MACD:", context.get("000001_MACD_default"))
        
        assert "000001_MA_5" in context
        assert float(context["000001_MA_5"]) == 37.0
        
        assert "000001_MACD_default" in context
        assert "DIF" in context["000001_MACD_default"]

if __name__ == "__main__":
    asyncio.run(test_indicator_calculation())
