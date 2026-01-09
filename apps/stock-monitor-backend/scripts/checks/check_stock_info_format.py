
import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock import StockInfo

async def check_stock_info():
    await db_manager.initialize()
    async with db_manager.session_factory() as session:
        # Check first 5 stocks
        stmt = select(StockInfo).limit(5)
        result = await session.execute(stmt)
        stocks = result.scalars().all()
        print("=== Sample Stocks ===")
        for s in stocks:
            print(f"Code: {s.code}, Name: {s.name}")
            
        # Check for 600724 (fuzzy search)
        stmt = select(StockInfo).where(StockInfo.code.like("%600724%"))
        result = await session.execute(stmt)
        match = result.scalars().first()
        if match:
            print(f"\nFound match: {match.code} - {match.name}")
        else:
            print("\nNo match found for 600724")

if __name__ == "__main__":
    asyncio.run(check_stock_info())
