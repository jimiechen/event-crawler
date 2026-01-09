
import asyncio
from sqlalchemy import select, func
from app.database import db_manager
from app.models.stock_daily import StockDaily

async def check_data():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        # Check count for 000001
        stmt = select(func.count()).where(StockDaily.code.like("%000001%"))
        count = await session.scalar(stmt)
        print(f"Count for 000001: {count}")

        # Check sample to see format
        stmt = select(StockDaily.code).limit(5)
        result = await session.execute(stmt)
        print(f"Sample codes: {result.scalars().all()}")
        
        # Check specifically for 002429
        stmt = select(StockDaily.code).where(StockDaily.code.like("%002429%")).limit(1)
        result = await session.execute(stmt)
        print(f"Code format for 002429: {result.scalar()}")

if __name__ == "__main__":
    asyncio.run(check_data())
