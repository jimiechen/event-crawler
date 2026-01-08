import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.volume_analysis_service import VolumeAnalysisService
from app.models.volume_analysis import StockVolumeBaseline
from app.services.stock_data_manager import StockDataManager
from app.models.stock_daily import StockDaily

@pytest_asyncio.fixture
async def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.mark.asyncio
async def test_save_baseline_updates_correctly(mock_session):
    """
    Test that save_baseline updates the baseline record correctly based on rules.
    """
    # Setup initial state
    code = "000001"
    existing_record = StockVolumeBaseline(
        code=code,
        last_3x_date=date(2023, 1, 1),
        last_3x_close=Decimal("10.00"),
        last_60d_low_vol_date=date(2023, 1, 1),
        last_60d_low_vol=Decimal("1000")
    )
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_record
    mock_session.execute.return_value = mock_result
    
    # New data to update
    baseline_data = {
        "latest_3x_record": {
            "date": date(2023, 2, 1), # Newer date
            "close": 12.00
        },
        "latest_low_vol_records": {
            "60": {
                "date": date(2023, 2, 5), # Newer date
                "vol": 800
            },
            "5": {
                "date": date(2023, 2, 10),
                "vol": 500
            }
        }
    }
    
    # Execute
    await VolumeAnalysisService.save_baseline(code, baseline_data, mock_session)
    
    # Verify updates
    assert existing_record.last_3x_date == date(2023, 2, 1)
    assert existing_record.last_3x_close == Decimal("12.0")
    
    assert existing_record.last_60d_low_vol_date == date(2023, 2, 5)
    assert existing_record.last_60d_low_vol == Decimal("800")
    
    # Verify new field added (was None implicitly)
    assert existing_record.last_5d_low_vol_date == date(2023, 2, 10)
    assert existing_record.last_5d_low_vol == Decimal("500")

@pytest.mark.asyncio
async def test_save_baseline_ignores_older_data(mock_session):
    """
    Test that save_baseline does NOT update if new data is older than existing.
    """
    code = "000001"
    existing_record = StockVolumeBaseline(
        code=code,
        last_3x_date=date(2023, 6, 1),
        last_3x_close=Decimal("15.00")
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_record
    mock_session.execute.return_value = mock_result
    
    # Older data
    baseline_data = {
        "latest_3x_record": {
            "date": date(2023, 1, 1), # Older
            "close": 10.00
        }
    }
    
    await VolumeAnalysisService.save_baseline(code, baseline_data, mock_session)
    
    # Verify NO change
    assert existing_record.last_3x_date == date(2023, 6, 1)
    assert existing_record.last_3x_close == Decimal("15.00")

@pytest.mark.asyncio
async def test_calculate_stock_uses_data_manager(mock_session):
    """
    Test that _calculate_stock_internal calls StockDataManager.get_stock_data.
    """
    code = "000001"
    
    # Mock StockDataManager
    with patch("app.services.volume_analysis_service.StockDataManager") as MockManagerClass:
        mock_manager = MockManagerClass.return_value
        
        # Mock get_stock_data return value
        mock_data = [
            StockDaily(code=code, trade_date=date(2023, 1, 1), close=Decimal("10"), vol=1000),
            StockDaily(code=code, trade_date=date(2023, 1, 2), close=Decimal("11"), vol=2000)
        ]
        mock_manager.get_stock_data = AsyncMock(return_value=mock_data)
        
        # We need to mock db_manager used inside the service
        with patch("app.services.volume_analysis_service.db_manager") as mock_db_manager:
            # We don't really need the session here since we mocked get_stock_data logic, 
            # but calculate_stock_internal uses session for other things (like checking score date).
            # Let's mock scalar result for date check to avoid skipping.
            mock_session.scalar.return_value = None # No previous score
            
            # Run
            result = await VolumeAnalysisService._calculate_stock_internal(code, mock_session)
            
            # Verify StockDataManager was initialized
            MockManagerClass.assert_called_once()
            
            # Verify get_stock_data was called
            mock_manager.get_stock_data.assert_called_with(code, limit=400)
            
            # Result should not be empty (unless logic fails elsewhere)
            # The calculation logic itself might fail if pandas not mocked or data insufficient.
            # But we are testing the data fetch delegation.
            # Given only 2 records, it might log warning "Insufficient data" if threshold is higher?
            # Code says: if len(daily_data) < 2: return should_skip
            # We provided 2, so it proceeds.
            
            assert result is not None
