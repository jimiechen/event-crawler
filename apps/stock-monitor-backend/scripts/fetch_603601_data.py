
import asyncio
import sys
import os
import akshare as ak
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import text
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.rule_engine_service import RuleEngineService
from app.config.settings import get_settings

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")

async def fetch_and_save_data():
    await db_manager.initialize()
    
    stock_code = "603601"
    start_date = "20251001"
    end_date = "20251210"
    
    logger.info(f"Fetching data for {stock_code} from {start_date} to {end_date}...")
    
    try:
        # Fetch data using akshare
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        
        if df.empty:
            logger.error("No data fetched!")
            return
            
        logger.info(f"Fetched {len(df)} rows.")
        
        # Transform and Save to CSV
        daily_dir = get_settings().csv_data_path
        daily_basic_dir = os.path.join(os.path.dirname(daily_dir), "daily_basic")
        
        os.makedirs(daily_dir, exist_ok=True)
        os.makedirs(daily_basic_dir, exist_ok=True)
        
        csv_filename = "603601.SH.csv"
        daily_csv_path = os.path.join(daily_dir, csv_filename)
        daily_basic_csv_path = os.path.join(daily_basic_dir, csv_filename)
        
        # Prepare CSV data lists
        daily_rows = []
        basic_rows = []
        
        data_list = []
        for _, row in df.iterrows():
            trade_date_val = row['日期']
            if isinstance(trade_date_val, str):
                trade_date = datetime.strptime(trade_date_val, "%Y-%m-%d").date()
            else:
                trade_date = trade_date_val
                if hasattr(trade_date, 'date'): # if datetime object
                    trade_date = trade_date.date()
            
            trade_date_str = trade_date.strftime("%Y-%m-%d")
            
            vol = int(row['成交量'])
            amount = float(row['成交额']) 
            amount_k = amount / 1000.0
            
            open_p = row['开盘']
            close_p = row['收盘']
            high_p = row['最高']
            low_p = row['最低']
            turnover = row['换手率']
            
            daily_rows.append({
                "交易日期": trade_date_str,
                "开盘价": open_p,
                "最高价": high_p,
                "最低价": low_p,
                "收盘价": close_p,
                "成交量(手)": vol,
                "成交额(千元)": amount_k
            })
            
            basic_rows.append({
                "交易日期": trade_date_str,
                "换手率(%)": turnover,
                "量比": 0
            })
            
            data_list.append({
                "code": stock_code,
                "trade_date": trade_date,
                "open": open_p,
                "close": close_p,
                "high": high_p,
                "low": low_p,
                "vol": vol,
                "amount": amount,
                "turnover_rate": turnover,
            })
                
        # Write CSVs
        logger.info(f"Writing CSVs to {daily_csv_path} and {daily_basic_csv_path}...")
        pd.DataFrame(daily_rows).to_csv(daily_csv_path, index=False, encoding='utf-8-sig')
        pd.DataFrame(basic_rows).to_csv(daily_basic_csv_path, index=False, encoding='utf-8-sig')

        # Insert into DB
        async with db_manager.get_session() as session:
            logger.info("Inserting data into stock_daily...")
            stmt = text("""
                INSERT INTO stock_daily (code, trade_date, open, close, high, low, vol, amount, turnover_rate)
                VALUES (:code, :trade_date, :open, :close, :high, :low, :vol, :amount, :turnover_rate)
                ON DUPLICATE KEY UPDATE
                open=VALUES(open), close=VALUES(close), high=VALUES(high), low=VALUES(low), 
                vol=VALUES(vol), amount=VALUES(amount), turnover_rate=VALUES(turnover_rate)
            """)
            
            for item in data_list:
                await session.execute(stmt, item)
            
            await session.commit()
            logger.info("Data inserted successfully.")
            
    except Exception as e:
        logger.error(f"Failed to fetch/save data: {e}")
        return

    # Now calculate scores for the target period
    logger.info("Recalculating scores for 603601...")
    
    start_dt = date(2025, 11, 20)
    end_dt = date(2025, 12, 10)
    
    target_dates = []
    current = start_dt
    while current <= end_dt:
        target_dates.append(current)
        current = current + timedelta(days=1)
    
    rule_service = RuleEngineService(db_manager)
    
    for target_date in target_dates:
        logger.info(f"Calculating for {target_date}...")
        try:
            await rule_service.calculate_daily_scores(target_date=target_date, force=True, stock_code=stock_code)
            logger.info(f"Completed scoring for {target_date}")
        except Exception as e:
            logger.error(f"Failed to calculate for {target_date}: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_and_save_data())
