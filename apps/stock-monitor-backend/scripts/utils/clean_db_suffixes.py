import asyncio
import sys
import os
from sqlalchemy import select, func, text, delete, and_

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.models.stock_daily import StockDaily
from app.models.stock import StockInfo

async def clean_db():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        print("Starting DB cleanup...")
        
        # 1. Clean StockInfo
        print("\nCleaning StockInfo...")
        stmt = select(StockInfo).where(StockInfo.code.like("%.%"))
        result = await session.execute(stmt)
        infos = result.scalars().all()
        
        for info in infos:
            clean_code = info.code.split(".")[0]
            print(f"Processing StockInfo {info.code} -> {clean_code}")
            
            # Check if clean code exists
            stmt = select(StockInfo).where(StockInfo.code == clean_code)
            existing = (await session.execute(stmt)).scalars().first()
            
            if existing:
                print(f"  Duplicate found. Deleting {info.code} (keeping {clean_code})")
                await session.delete(info)
            else:
                print(f"  Updating {info.code} to {clean_code}")
                info.code = clean_code
                session.add(info)
        
        await session.commit()
        
        # 2. Clean StockDaily
        print("\nCleaning StockDaily...")
        # Get all records with suffix
        stmt = select(StockDaily).where(StockDaily.code.like("%.%"))
        result = await session.execute(stmt)
        dailies = result.scalars().all()
        
        print(f"Found {len(dailies)} StockDaily records with suffix.")
        
        processed_count = 0
        deleted_count = 0
        updated_count = 0
        
        for d in dailies:
            clean_code = d.code.split(".")[0]
            
            # Check if record exists for clean_code + trade_date
            stmt = select(StockDaily).where(
                and_(
                    StockDaily.code == clean_code,
                    StockDaily.trade_date == d.trade_date
                )
            )
            existing = (await session.execute(stmt)).scalars().first()
            
            if existing:
                # Duplicate exists, delete this one
                await session.delete(d)
                deleted_count += 1
            else:
                # Update code
                d.code = clean_code
                session.add(d)
                updated_count += 1
            
            processed_count += 1
            if processed_count % 100 == 0:
                print(f"Processed {processed_count} records...")
                await session.commit() # Commit periodically
        
        await session.commit()
        print(f"StockDaily Cleanup Done. Deleted: {deleted_count}, Updated: {updated_count}")

if __name__ == "__main__":
    asyncio.run(clean_db())
