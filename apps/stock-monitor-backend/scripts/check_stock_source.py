import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock import StockInfo, WencaiStock
from sqlalchemy import select

async def check_info():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        print("Checking StockInfo...")
        stmt = select(StockInfo).where(StockInfo.code == "603601")
        result = await session.execute(stmt)
        info = result.scalars().first()
        if info:
            print(f"Code: {info.code}")
            print(f"Name: {info.name}")
            print(f"Source: {info.source}")
        else:
            print("Stock not found in StockInfo")
            
        print("\nChecking WencaiStock...")
        stmt_wencai = select(WencaiStock).where(WencaiStock.stock_code == "603601")
        result_wencai = await session.execute(stmt_wencai)
        wencai_records = result_wencai.scalars().all()
        if wencai_records:
            print(f"Found {len(wencai_records)} Wencai records")
            for r in wencai_records[:5]:
                print(f"  Date: {r.created_at}, Concept: {r.concept}")
        else:
            print("No Wencai records found")

if __name__ == "__main__":
    asyncio.run(check_info())
