import asyncio
import os
import sys
import pandas as pd
from datetime import date, datetime
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from app.services.data_merge_service import DataMergeService
from app.database import db_manager
from loguru import logger

# Mock Settings
from app.config.settings import settings
settings.csv_data_path_stock_daily = "/Volumes/MacintoshHD/data/daily"

TEST_CODE = "000001.SZ"
TEST_CSV_PATH = f"/Volumes/MacintoshHD/data/daily/TEST_{TEST_CODE}.csv"

async def test_gap_filling():
    logger.info("Starting gap filling test...")
    
    # 1. Prepare CSV with initial data (up to 2024-01-04)
    # Use Chinese columns to match real environment
    df = pd.DataFrame({
        '股票代码': [TEST_CODE],
        '交易日期': ['20240104'],
        '开盘价': [10.0],
        '最高价': [10.2],
        '最低价': [9.9],
        '收盘价': [10.1],
        '昨收价': [10.0],
        '涨跌额': [0.1],
        '涨跌幅': [1.0],
        '成交量(手)': [1000],
        '成交额(千元)': [10000]
    })
    
    df.to_csv(TEST_CSV_PATH, index=False)
    logger.info(f"Created test CSV at {TEST_CSV_PATH} with date 20240104")
    
    # 2. Prepare new data to append (2024-01-08)
    # Gap: 2024-01-05 (Fri) is missing.
    new_data = {
        'ts_code': TEST_CODE,
        'trade_date': '20240108',
        'open': 10.5,
        'close': 10.6,
        'high': 10.7,
        'low': 10.4,
        'vol': 1200,
        'amount': 12000,
        'change': 0.1,
        'pct_chg': 1.0
    }
    
    # 3. Initialize Service
    async with db_manager.get_session() as session:
        service = DataMergeService(session)
        
        # Monkeypatch _get_csv_path to return our test path
        service._get_csv_path = MagicMock(return_value=TEST_CSV_PATH)
        
        # 4. Call _append_to_csv
        logger.info("Calling _append_to_csv...")
        await service._append_to_csv(TEST_CODE, new_data)
        
    # 5. Verify CSV content
    df_result = pd.read_csv(TEST_CSV_PATH)
    logger.info("Result CSV content:")
    print(df_result)
    
    date_col = '交易日期' if '交易日期' in df_result.columns else 'trade_date'
    dates = df_result[date_col].astype(str).tolist()
    # Normalize dates
    dates = [d.replace('-', '').replace('.0', '') for d in dates]
    
    if '20240105' in dates:
        logger.success("SUCCESS: 20240105 was filled!")
    else:
        logger.error("FAILURE: 20240105 was NOT filled.")
        
    # Cleanup
    if os.path.exists(TEST_CSV_PATH):
        os.remove(TEST_CSV_PATH)
        logger.info("Cleaned up test file.")

if __name__ == "__main__":
    asyncio.run(test_gap_filling())
