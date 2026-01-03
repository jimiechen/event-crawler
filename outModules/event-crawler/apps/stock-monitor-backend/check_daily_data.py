
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import db_manager
from sqlalchemy import select, func, desc
from app.models.stock_daily import StockDaily

async def check_daily_data():
    try:
        async with db_manager.get_session() as session:
            stmt = select(func.count(StockDaily.id)).where(StockDaily.code == '000001')
            count = (await session.execute(stmt)).scalar()
            print(f"Daily data records for 000001: {count}")
            
            if count > 0:
                stmt = select(StockDaily).where(StockDaily.code == '000001').order_by(desc(StockDaily.trade_date)).limit(5)
                result = await session.execute(stmt)
                latest = result.scalars().all()
                print("\nLatest 5 daily records:")
                for item in latest:
                    print(f"Date: {item.trade_date}, Open: {item.open}, Close: {item.close}, Vol: {item.vol}")
    except Exception as e:
        print(f"Error checking daily data: {e}")

if __name__ == "__main__":
    asyncio.run(check_daily_data())
