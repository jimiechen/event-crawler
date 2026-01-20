import asyncio
import os
import sys

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.database import db_manager
from sqlalchemy import text

async def check_data():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        # 1. Check wencai_stocks count for today
        print("--- Checking wencai_stocks ---")
        result = await session.execute(text("SELECT count(*) FROM wencai_stocks WHERE date(created_at) = CURDATE()"))
        count = result.scalar()
        print(f"wencai_stocks count (today): {count}")

        # 2. Check stock_score_result count for today
        print("\n--- Checking stock_score_result ---")
        result = await session.execute(text("SELECT count(*) FROM stock_score_result WHERE date(created_at) = CURDATE()"))
        count = result.scalar()
        print(f"stock_score_result count (today): {count}")

        # 3. Check volume_analysis_result count for today
        print("\n--- Checking volume_analysis_result ---")
        result = await session.execute(text("SELECT count(*) FROM volume_analysis_result WHERE date(created_at) = CURDATE()"))
        count = result.scalar()
        print(f"volume_analysis_result count (today): {count}")
        
        result = await session.execute(text("SELECT count(distinct code) FROM volume_analysis_result WHERE date(created_at) = CURDATE()"))
        unique_count = result.scalar()
        print(f"volume_analysis_result unique stocks (today): {unique_count}")
        
        # 4. Check stock_volume_baseline count (total)
        print("\n--- Checking stock_volume_baseline ---")
        result = await session.execute(text("SELECT count(*) FROM stock_volume_baseline"))
        count = result.scalar()
        print(f"stock_volume_baseline count (total): {count}")

        # 5. Check specific stocks
        stocks = ['600016', '600755', '600055']
        print(f"\n--- Checking specific stocks: {stocks} ---")
        for stock in stocks:
            print(f"Checking {stock}...")
            # Check if exists in wencai_stocks
            res = await session.execute(text("SELECT count(*) FROM wencai_stocks WHERE stock_code = :code AND date(created_at) = CURDATE()"), {"code": stock})
            in_wencai = res.scalar()
            print(f"  In wencai_stocks: {in_wencai}")
            
            # Check if exists in stock_volume_baseline
            res = await session.execute(text("SELECT count(*) FROM stock_volume_baseline WHERE code = :code"), {"code": stock})
            in_baseline = res.scalar()
            print(f"  In stock_volume_baseline: {in_baseline}")

            # Check local data availability (simulated check via stock_daily or similar if possible, but baseline check is good proxy)
            
if __name__ == "__main__":
    asyncio.run(check_data())
