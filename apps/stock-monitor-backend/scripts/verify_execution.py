
import sys
import os
import asyncio
import pandas as pd
from datetime import datetime, date
from sqlalchemy import select, text, func

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock_daily import StockDaily
from loguru import logger

async def main():
    await db_manager.initialize()
    
    # 1. Check Wencai Files
    wencai_dir = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"
    files = os.listdir(wencai_dir)
    wencai_dates = []
    for f in files:
        if f.startswith("wencai_") and f.endswith(".csv"):
            d_str = f.replace("wencai_", "").replace(".csv", "")
            try:
                d = datetime.strptime(d_str, "%Y%m%d").date()
                wencai_dates.append(d)
            except:
                pass
    wencai_dates.sort()
    
    print(f"\n[1] Wencai CSV Check ({len(wencai_dates)} files found):")
    print(f"Latest file: {wencai_dates[-1] if wencai_dates else 'None'}")
    
    # Check specific gaps identified earlier
    missing_dates = []
    check_start = date(2025, 12, 11)
    check_end = date(2026, 1, 16)
    
    current = check_start
    while current <= check_end:
        if current.weekday() < 5: # Weekday
            if current not in wencai_dates:
                missing_dates.append(current)
        current = current.fromordinal(current.toordinal() + 1)
        
    if missing_dates:
        print(f"Missing Wencai Dates (Weekdays): {[d.strftime('%Y-%m-%d') for d in missing_dates]}")
    else:
        print("All weekdays from 2025-12-11 to 2026-01-16 have Wencai CSV files.")

    # 2. Check Database Stock Daily for Sample Stock
    sample_code = "002775"
    print(f"\n[2] Database Check for Sample Stock {sample_code}:")
    async with db_manager.get_session() as session:
        stmt = select(func.max(StockDaily.trade_date)).where(StockDaily.code == sample_code)
        result = await session.execute(stmt)
        max_date = result.scalar()
        print(f"Max Trade Date in DB: {max_date}")
        
        # Check count of records in range
        stmt_count = select(func.count(StockDaily.id)).where(
            StockDaily.code == sample_code,
            StockDaily.trade_date >= check_start,
            StockDaily.trade_date <= check_end
        )
        result_count = await session.execute(stmt_count)
        count = result_count.scalar()
        print(f"Records count in range ({check_start} to {check_end}): {count}")

    # 3. Check Daily CSV File
    daily_csv_dir = "/Volumes/MacintoshHD/data/daily"
    # Try suffix
    possible_names = [f"{sample_code}.csv", f"{sample_code}.SZ.csv", f"{sample_code}.SH.csv"]
    found_csv = None
    for name in possible_names:
        p = os.path.join(daily_csv_dir, name)
        if os.path.exists(p):
            found_csv = p
            break
            
    print(f"\n[3] Daily CSV Check for {sample_code}:")
    if found_csv:
        print(f"Found CSV: {found_csv}")
        try:
            df = pd.read_csv(found_csv)
            # Normalize column name 'trade_date'
            if 'trade_date' not in df.columns:
                 # Try finding date column
                 cols = df.columns
                 for c in cols:
                     if 'date' in c.lower() or '日期' in c:
                         df.rename(columns={c: 'trade_date'}, inplace=True)
                         break
            
            if 'trade_date' in df.columns:
                # Convert to string for comparison
                df['trade_date'] = df['trade_date'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace('-', '')
                
                last_date = df['trade_date'].max()
                print(f"Last Date in CSV: {last_date}")
                
                # Check 20260116
                has_target = '20260116' in df['trade_date'].values
                print(f"Has 2026-01-16 data: {has_target}")
            else:
                print("Could not find trade_date column in CSV")
        except Exception as e:
            print(f"Error reading CSV: {e}")
    else:
        print(f"CSV file not found in {daily_csv_dir}")

if __name__ == "__main__":
    asyncio.run(main())
