
import asyncio
from sqlalchemy import select
from app.database import db_manager
from app.models.stock import StockInfo

async def check_active():
    await db_manager.initialize()
    async with db_manager.session_factory() as session:
        code = "600724.SH"
        stmt = select(StockInfo).where(StockInfo.code == code)
        result = await session.execute(stmt)
        stock = result.scalars().first()
        
        if stock:
            print(f"Stock: {stock.name} ({stock.code})")
            print(f"Is Active: {stock.is_active}")
        else:
            print("Stock not found in stock_info.")

if __name__ == "__main__":
    asyncio.run(check_active())
