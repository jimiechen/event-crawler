import asyncio
import sys
import os
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.models.stock import StockInfo

async def main():
    async with db_manager.get_session() as session:
        stmt = select(StockInfo).where(StockInfo.code == "000881")
        result = await session.execute(stmt)
        stock = result.scalar_one_or_none()
        
        if stock:
            print(f"StockInfo for 000881:")
            print(f"Volume Anomaly Score: {stock.volume_anomaly_score}")
            print(f"Bonus Items: {stock.bonus_items}")
        else:
            print("Stock 000881 not found")

if __name__ == "__main__":
    asyncio.run(main())
