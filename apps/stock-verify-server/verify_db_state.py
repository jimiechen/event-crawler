
import asyncio
from sqlalchemy import text
from app.core.database import get_db

async def verify():
    async for session in get_db():
        print("--- Verification Start ---")
        
        # Check wencai_stocks count
        res = await session.execute(text("SELECT count(*) FROM wencai_stocks"))
        count = res.scalar()
        print(f"wencai_stocks count: {count} (Expected: 12)")
        
        # Check 603601 existence
        res = await session.execute(text("SELECT count(*) FROM wencai_stocks WHERE stock_code='603601'"))
        has_603601 = res.scalar()
        print(f"603601 in wencai_stocks: {has_603601} (Expected: 1)")
        
        # Check score results for 2025-11-19
        res = await session.execute(text("SELECT count(*) FROM stock_score_result WHERE trade_date='2025-11-19'"))
        score_count_19 = res.scalar()
        print(f"Scores on 2025-11-19: {score_count_19} (Expected: 1)")
        
        # Check score results for 2025-11-20
        res = await session.execute(text("SELECT count(*) FROM stock_score_result WHERE trade_date='2025-11-20'"))
        score_count_20 = res.scalar()
        print(f"Scores on 2025-11-20: {score_count_20} (Expected: 12)")
        
        print("--- Verification End ---")
        break

if __name__ == "__main__":
    asyncio.run(verify())
