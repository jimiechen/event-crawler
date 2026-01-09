import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

# DB Config from .env
DB_USER = "root"
DB_PASSWORD = "12345678"
DB_HOST = "192.168.1.6"
DB_PORT = "3306"
DB_DATABASE = "stock_monitor_new"

# Async MySQL URL
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

async def verify_data():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            print("\n--- Checking Stock: 600724 ---")
            
            # 1. Check Score
            print("Checking Score...")
            result = await session.execute(text("SELECT code, total_score, trade_date FROM stock_score_result WHERE code LIKE '%600724%' ORDER BY trade_date DESC LIMIT 1"))
            score_row = result.fetchone()
            if score_row:
                print(f"Score Result: Code={score_row[0]}, Score={score_row[1]}, Date={score_row[2]}")
            else:
                print("❌ No score found for 600724")

            # 2. Check Baseline
            print("\nChecking Baseline...")
            result = await session.execute(text("SELECT * FROM stock_volume_baseline WHERE code LIKE '%600724%' LIMIT 1"))
            baseline_row = result.fetchone()
            if baseline_row:
                # Get column names
                keys = result.keys()
                row_dict = dict(zip(keys, baseline_row))
                print(f"Baseline Data Keys: {list(row_dict.keys())}")
                print(f"Baseline Data Values: {row_dict}")
                
                # Check for nulls
                null_fields = [k for k, v in row_dict.items() if v is None]
                if null_fields:
                    print(f"❌ Null fields in baseline: {null_fields}")
                else:
                    print("✅ No null fields in baseline")
                    # Print some key fields
                    print(f"  avg_volume_250d: {row_dict.get('avg_volume_250d')}")
                    print(f"  max_volume_250d: {row_dict.get('max_volume_250d')}")
                    print(f"  low_volume_threshold: {row_dict.get('low_volume_threshold')}")
            else:
                print("❌ No baseline found for 600724")
                
            # 3. Check Daily Data Count
            print("\nChecking Daily Data...")
            result = await session.execute(text("SELECT count(*), max(trade_date) FROM stock_daily WHERE code LIKE '%600724%'"))
            daily_row = result.fetchone()
            print(f"Daily Data: Count={daily_row[0]}, Max Date={daily_row[1]}")
            
            # 4. Check Incremental Sync (Check if we have recent data for other stocks too)
            print("\nChecking Recent Data for other stocks...")
            result = await session.execute(text("SELECT max(trade_date) FROM stock_daily"))
            max_date = result.scalar()
            print(f"Overall Max Date in DB: {max_date}")

        await engine.dispose()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_data())
