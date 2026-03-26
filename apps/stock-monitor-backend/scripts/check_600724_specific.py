import sys
import os
sys.path.append(os.getcwd())

import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock import StockInfo

async def check_stock():
    await db_manager.initialize()
    async with db_manager.session_factory() as session:
        # Check for 600724
        stmt1 = select(StockInfo).where(StockInfo.code == "600724")
        result1 = await session.execute(stmt1)
        stock1 = result1.scalars().first()
        print(f"Checking '600724': Found = {stock1 is not None}")
        if stock1:
            print(f"  Name: {stock1.name}, Is Active: {stock1.is_active}")

        # Check for 600724.SH
        stmt2 = select(StockInfo).where(StockInfo.code == "600724.SH")
        result2 = await session.execute(stmt2)
        stock2 = result2.scalars().first()
        print(f"Checking '600724.SH': Found = {stock2 is not None}")
        if stock2:
            print(f"  Name: {stock2.name}, Is Active: {stock2.is_active}")

if __name__ == "__main__":
    asyncio.run(check_stock())
