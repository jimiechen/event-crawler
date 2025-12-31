import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.volume_analysis import StockVolumeBaseline
from sqlalchemy import select, func

async def main():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        result = await session.execute(select(func.count(StockVolumeBaseline.code)))
        count = result.scalar()
        print(f"Total records in stock_volume_baseline: {count}")
        
        # Show sample data
        result = await session.execute(select(StockVolumeBaseline).limit(5))
        records = result.scalars().all()
        for record in records:
            print(f"Code: {record.code}, 3x_date: {record.last_3x_date}, 2x_date: {record.last_2x_date}")

if __name__ == "__main__":
    asyncio.run(main())
