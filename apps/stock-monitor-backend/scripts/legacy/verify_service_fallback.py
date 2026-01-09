import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
from app.services.stock_service import StockService
from app.models.stock import StockInfo, StockData

class TestStockService(unittest.TestCase):
    def setUp(self):
        self.mock_session = AsyncMock()
        self.service = StockService(self.mock_session)
        # Mock repositories
        self.service.stock_repo = AsyncMock()
        self.service.stock_data_repo = AsyncMock()
        self.service.dedup_repo = AsyncMock()
        self.service.dedup_service = AsyncMock()

    def test_get_stock_info_fallback(self):
        async def run_test():
            # Setup: find_by_code returns None for "600000", but returns something for "600000.SH"
            self.service.stock_repo.find_by_code.side_effect = [None, StockInfo(code="600000.SH", name="Test")]
            
            result = await self.service.get_stock_info("600000")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.code, "600000.SH")
            # Verify calls
            # First call with 600000
            # Second call with 600000.SH
            self.assertEqual(self.service.stock_repo.find_by_code.call_count, 2)
            self.service.stock_repo.find_by_code.assert_any_call("600000")
            self.service.stock_repo.find_by_code.assert_any_call("600000.SH")
            
        asyncio.run(run_test())

    def test_get_stock_data_fallback(self):
        async def run_test():
            # Setup: find_by_code returns [] for "600000", but returns [data] for "600000.SH"
            self.service.stock_data_repo.find_by_code.side_effect = [[], [StockData(code="600000.SH")]]
            
            result = await self.service.get_stock_data("600000")
            
            self.assertTrue(len(result) > 0)
            self.assertEqual(result[0].code, "600000.SH")
            
            self.assertEqual(self.service.stock_data_repo.find_by_code.call_count, 2)
            
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
