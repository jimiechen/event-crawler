import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db_session

@pytest.mark.asyncio
async def test_api_integration_calls_pathway():
    """测试API集成 - 确保调用Pathway引擎"""
    
    # Mock DB Session for dependency injection
    async def mock_get_db():
        session = AsyncMock()
        # Setup execute return value to be a MagicMock (sync) not AsyncMock
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        result_mock.scalars.return_value.first.return_value = None
        result_mock.fetchone.return_value = None
        session.execute.return_value = result_mock
        
        # AsyncSession.add is sync
        session.add = MagicMock()
        
        yield session
        
    app.dependency_overrides[get_db_session] = mock_get_db
    
    # Mock global components to prevent startup errors
    with patch('app.main.db_manager') as mock_db_manager, \
         patch('app.main.scheduler_service') as mock_scheduler, \
         patch('app.main.executor') as mock_executor:
         
        # Setup mocks
        mock_db_manager.initialize = AsyncMock()
        mock_db_manager.create_tables = AsyncMock()
        mock_db_manager.health_check = AsyncMock(return_value=True)
        # Mock get_session to return an async context manager that yields a mock session
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_scheduler.start = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        
        mock_executor.start = MagicMock()
        mock_executor.shutdown = MagicMock()

        # Mock the engine method to verify it's called
        with patch('app.services.pathway_engine.PathwayVolumePriceEngine.process_realtime_batch', new_callable=AsyncMock) as mock_process:
            
            # Use ASGITransport for newer httpx versions
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                payload = {
                    "data_list": [
                        {
                            "stock_code": "600519",
                            "price": 2000.0,
                            "change_percent": 2.0,
                            "volume": 500,
                            "turnover": 0.1,
                            "change_amount": 40.0,
                            "high": 2010.0,
                            "low": 1990.0,
                            "open_price": 1995.0,
                            "prev_close": 1960.0
                        }
                    ]
                }
                
                # Call the API
                response = await ac.post("/api/v1/stocks/data/batch", json=payload)
                
                # Print response for debugging if failed
                if response.status_code != 200:
                    print(f"Response error: {response.text}")
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] == 1
                
                # Allow event loop to run pending tasks (since we used asyncio.create_task)
                await asyncio.sleep(0.1)
                
                # Verify process_realtime_batch was called
                mock_process.assert_called_once()
                args = mock_process.call_args[0][0]
                assert args[0]['stock_code'] == "600519"
