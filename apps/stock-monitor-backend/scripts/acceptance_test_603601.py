import asyncio
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging
from sqlalchemy import text, select

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from app.config.settings import get_settings
from app.database import DatabaseManager
from app.services.monitor_service import MonitorService
from app.services.stock_sync_service import StockSyncService
from app.services.rule_engine_service import RuleEngineService
from app.services.volume_analysis_service import VolumeAnalysisService
from app.models.stock import WencaiStock
from app.models.stock_daily import StockDaily

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Database Manager
db_manager = DatabaseManager()

STOCK_CODE = "603601"
STOCK_NAME = "再升科技"
CSV_DIR = get_settings().csv_data_path
CSV_PATH = os.path.join(CSV_DIR, f"{STOCK_CODE}.SH.csv")

async def clear_data():
    """Phase 1: Clear Global Data for 603601"""
    logger.info("--- Phase 1: Clearing Global Data for %s ---", STOCK_CODE)
    async with db_manager.get_session() as session:
        # Delete from various tables
        tables = [
            "wencai_stocks", "monitor_list", "stock_daily", 
            "stock_score_results", "analysis_logs", "wencai_data_dedup"
        ]
        
        for table in tables:
            await session.execute(text(f"DELETE FROM {table} WHERE stock_code = :code OR code = :code"), {"code": STOCK_CODE})
            # Also try with suffix just in case
            await session.execute(text(f"DELETE FROM {table} WHERE stock_code = :code OR code = :code"), {"code": f"{STOCK_CODE}.SH"})
            
        await session.commit()
    logger.info("Data cleared successfully.")

def prepare_csv():
    """Phase 1.5: Prepare CSV Data"""
    logger.info("--- Phase 1.5: Preparing CSV Data ---")
    if not os.path.exists(CSV_DIR):
        os.makedirs(CSV_DIR)
        
    # Generate synthetic data if not exists or force overwrite for test
    # Let's generate 200 days of data ending yesterday
    end_date = datetime.now().date() - timedelta(days=1)
    dates = [end_date - timedelta(days=x) for x in range(200)]
    dates.reverse()
    
    data = []
    price = 10.0
    for d in dates:
        change = np.random.uniform(-0.05, 0.05)
        open_p = price * (1 + np.random.uniform(-0.01, 0.01))
        close_p = price * (1 + change)
        high_p = max(open_p, close_p) * (1 + np.random.uniform(0, 0.02))
        low_p = min(open_p, close_p) * (1 - np.random.uniform(0, 0.02))
        vol = int(np.random.uniform(10000, 50000))
        amount = vol * close_p * 100
        
        data.append({
            "ts_code": f"{STOCK_CODE}.SH",
            "trade_date": d.strftime("%Y%m%d"),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "pre_close": round(price, 2),
            "change": round(close_p - price, 2),
            "pct_chg": round(change * 100, 2),
            "vol": vol,
            "amount": round(amount, 2)
        })
        price = close_p
        
    df = pd.DataFrame(data)
    # Tushare format often uses ts_code, trade_date, open, high, low, close, vol, amount
    # Our sync service handles mapping.
    df.to_csv(CSV_PATH, index=False)
    logger.info(f"CSV generated at {CSV_PATH} with {len(df)} rows.")

async def simulate_wencai_search():
    """Phase 2: Simulate Wencai Search & Add to Pool"""
    logger.info("--- Phase 2: Simulating Wencai Search & Adding to Pool ---")
    async with db_manager.get_session() as session:
        # 1. Simulate Wencai Crawler Result
        wencai_stock = WencaiStock(
            stock_code=STOCK_CODE,
            stock_name=STOCK_NAME,
            created_at=datetime.now(),
            concept="模拟概念",
            industry="模拟行业",
            crawl_batch_id="test_batch_001"
        )
        session.add(wencai_stock)
        await session.commit()
        logger.info("Simulated Wencai crawler result inserted.")
        
        # 2. Add to Monitor Pool (Simulating 'Add to Pool' action)
        monitor_service = MonitorService(session)
        # Using a high priority to simulate "selected" stock
        await monitor_service.add_monitor(
            stock_code=STOCK_CODE, 
            priority=9, 
            auto_create_stock=True
        )
        await session.commit()
    logger.info("Stock added to Monitor Pool.")

async def load_historical_data():
    """Phase 3: Load Historical CSV Data"""
    logger.info("--- Phase 3: Loading Historical CSV Data ---")
    async with db_manager.get_session() as session:
        sync_service = StockSyncService(session)
        # Assuming end_date covers the generated CSV
        result = await sync_service.sync_csv_single(
            code=STOCK_CODE, 
            days=300, 
            end_date_str=datetime.now().strftime("%Y-%m-%d")
        )
        logger.info(f"CSV Sync Result: {result}")
        if not result.get('success'):
            logger.error("CSV Sync Failed!")
            return

async def calculate_scores_and_analysis():
    """Phase 4: Calculate Scores and Run Analysis"""
    logger.info("--- Phase 4: Initial Scoring & Analysis ---")
    async with db_manager.get_session() as session:
        # 1. Score
        rule_service = RuleEngineService(session)
        target_date = datetime.now().date() - timedelta(days=1) # Score for "yesterday" (last data point)
        
        # We need to make sure we score the date that actually has data.
        # Our CSV generator ended yesterday.
        logger.info(f"Executing scoring for date: {target_date}")
        result = await rule_service.execute_scoring(target_date=target_date, force=True)
        logger.info(f"Scoring Result: {result}")
        
        # 2. Volume/Pattern Analysis
        logger.info("Running Volume Analysis...")
        vol_result = await VolumeAnalysisService.calculate_stock(STOCK_CODE, session)
        logger.info(f"Volume Analysis Result: {vol_result}")

async def simulate_daily_update():
    """Phase 5: Simulate Daily Update (Next Day)"""
    logger.info("--- Phase 5: Simulating Daily Update (Next Day) ---")
    
    # 1. Generate "Today's" Data (The "Next Day" relative to CSV)
    today = datetime.now().date()
    async with db_manager.get_session() as session:
        # Get last close
        stmt = select(StockDaily).where(StockDaily.code == STOCK_CODE).order_by(StockDaily.trade_date.desc()).limit(1)
        last_daily = (await session.execute(stmt)).scalar()
        last_close = last_daily.close if last_daily else 10.0
        
        # Simulate a Bullish Engulfing or Big Rise
        new_close = float(last_close) * 1.05
        new_open = float(last_close) * 0.99
        new_high = new_close * 1.01
        new_low = new_open * 0.99
        new_vol = 100000 # High volume
        
        new_daily = StockDaily(
            code=STOCK_CODE,
            trade_date=today,
            open=Decimal(new_open),
            high=Decimal(new_high),
            low=Decimal(new_low),
            close=Decimal(new_close),
            vol=new_vol,
            amount=Decimal(new_vol * new_close)
        )
        session.add(new_daily)
        await session.commit()
        logger.info(f"Simulated new daily data for {today}")
        
        # 2. Re-run Scoring
        logger.info(f"Re-running scoring for {today}")
        rule_service = RuleEngineService(session)
        score_res = await rule_service.execute_scoring(target_date=today, force=True)
        logger.info(f"New Scoring Result: {score_res}")
        
        # 3. Check for Alerts (This would usually be in logs or a specific alert table)
        # Here we check analysis logs
        logger.info("Checking Analysis Logs...")
        log_stmt = text(f"SELECT * FROM analysis_logs WHERE code = '{STOCK_CODE}' ORDER BY created_at DESC LIMIT 5")
        logs = (await session.execute(log_stmt)).fetchall()
        for log in logs:
            logger.info(f"Log: {log}")

async def main():
    logger.info("Starting Acceptance Test for 603601...")
    
    # Initialize Database Connection
    await db_manager.initialize()
    
    await clear_data()
    prepare_csv()
    await simulate_wencai_search()
    await load_historical_data()
    await calculate_scores_and_analysis()
    await simulate_daily_update()
    
    logger.info("Acceptance Test Completed.")

if __name__ == "__main__":
    asyncio.run(main())
