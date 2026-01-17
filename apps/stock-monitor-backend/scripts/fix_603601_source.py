import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock import StockInfo
from sqlalchemy import select, update

async def fix_stock_source():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        print("Updating StockInfo for 603601...")
        stmt = select(StockInfo).where(StockInfo.code == "603601")
        result = await session.execute(stmt)
        info = result.scalars().first()
        if info:
            print(f"Current Source: {info.source}")
            info.source = 'wencai'
            await session.commit()
            print("Updated Source to 'wencai'")
        else:
            print("Stock not found")

if __name__ == "__main__":
    asyncio.run(fix_stock_source())
