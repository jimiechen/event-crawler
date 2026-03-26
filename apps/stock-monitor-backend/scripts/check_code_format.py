
import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock import WencaiStock
from app.models.stock_daily import StockScoreResult

async def check_code_format():
    await db_manager.initialize()
    
    # Use async with for context manager
    async with db_manager.get_session() as session:
        try:
            # Check WencaiStock
            stmt = select(WencaiStock.stock_code).limit(5)
            result = await session.execute(stmt)
            ws_codes = result.scalars().all()
            print(f"WencaiStock codes: {ws_codes}")
            
            # Check StockScoreResult
            stmt = select(StockScoreResult.code).limit(5)
            result = await session.execute(stmt)
            ss_codes = result.scalars().all()
            print(f"StockScoreResult codes: {ss_codes}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_code_format())
