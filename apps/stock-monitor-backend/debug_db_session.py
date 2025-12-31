
import asyncio
import sys
import os
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.database import db_manager, get_db_session
from app.models.stock_daily import StockDaily

async def main():
    print("Initializing DB...")
    await db_manager.initialize()
    
    code = "002735"
    print(f"Querying for code: '{code}'")
    
    async with db_manager.get_session() as session:
        stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(250)
        result = await session.execute(stmt)
        records = result.scalars().all()
        print(f"Records found: {len(records)}")
        
        if records:
            print(f"First record: {records[0].trade_date} - {records[0].close}")
            
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
