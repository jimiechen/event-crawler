
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.local_data_service import LocalDataService
from app.repositories.stock_daily_repository import StockDailyRepository
from app.config.settings import get_settings
from sqlalchemy import text
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

from datetime import datetime

async def check_data():
    print(f"Daily Dir: {LocalDataService.get_daily_dir()}")
    
    # Debug loading for 600016
    code = "600016"
    end_date = datetime.strptime("2025-11-20", "%Y-%m-%d").date()
    
    print(f"\n--- Debugging {code} with end_date={end_date} ---")
    data = await LocalDataService.get_daily_data(code, limit=250, end_date=end_date)
    print(f"Loaded {len(data)} records for {code}")
    if data:
        print(f"Sample: {data[0]}")
        
        # Try saving
        print("Attempting to save to DB...")
        repo = StockDailyRepository(db_manager)
        try:
            saved_count = await repo.batch_save_daily_data(data)
            print(f"Saved count: {saved_count}")
        except Exception as e:
            print(f"Save failed: {e}")
    
    async with db_manager.get_session() as session:
        # Check 600080
        code = "600080"
        print(f"\nChecking data for {code}...")
        
        # Check baseline
        result_baseline = await session.execute(text(f"SELECT * FROM stock_volume_baseline WHERE code = '{code}'"))
        baseline = result_baseline.first()
        print(f"Baseline for {code}: {baseline}")
        
        # Check score for 2025-11-20
        result_score = await session.execute(text(f"SELECT * FROM stock_score_result WHERE code = '{code}' AND trade_date = '2025-11-20'"))
        score = result_score.first()
        print(f"Score for {code} on 2025-11-20: {score}")
        
        # Check volume analysis
        result_vol = await session.execute(text(f"SELECT COUNT(*) FROM volume_analysis_result WHERE code = '{code}'"))
        vol_count = result_vol.scalar()
        print(f"Volume analysis count for {code}: {vol_count}")

if __name__ == "__main__":
    print("Starting check...")
    try:
        asyncio.run(check_data())
    except Exception as e:
        print(f"Error: {e}")
