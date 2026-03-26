import asyncio
import sys
import os
from sqlalchemy import select, func, text

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.models.stock_daily import StockDaily
from app.models.stock import StockInfo
from app.models.volume_analysis import VolumeAnalysisResult, StockVolumeBaseline

async def check_suffixes():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        print("Checking for suffixes in DB...")
        
        # StockDaily
        print("Checking StockDaily...")
        stmt = select(func.count()).where(StockDaily.code.like("%.%"))
        count = await session.scalar(stmt)
        print(f"StockDaily records with suffix: {count}")
        
        if count > 0:
            stmt = select(StockDaily.code).where(StockDaily.code.like("%.%")).limit(5)
            rows = (await session.execute(stmt)).scalars().all()
            print(f"Sample: {rows}")

        # StockInfo
        print("\nChecking StockInfo...")
        stmt = select(func.count()).where(StockInfo.code.like("%.%"))
        count = await session.scalar(stmt)
        print(f"StockInfo records with suffix: {count}")

        # VolumeAnalysisResult
        print("\nChecking VolumeAnalysisResult...")
        stmt = select(func.count()).where(VolumeAnalysisResult.code.like("%.%"))
        count = await session.scalar(stmt)
        print(f"VolumeAnalysisResult records with suffix: {count}")

        # StockVolumeBaseline
        print("\nChecking StockVolumeBaseline...")
        stmt = select(func.count()).where(StockVolumeBaseline.code.like("%.%"))
        count = await session.scalar(stmt)
        print(f"StockVolumeBaseline records with suffix: {count}")

if __name__ == "__main__":
    asyncio.run(check_suffixes())
