import asyncio
import sys
import os
from datetime import date, timedelta
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.rule_engine_service import RuleEngineService
from app.services.volume_analysis_service import VolumeAnalysisService
from app.models.stock import StockInfo

async def generate_tags_for_date(target_date):
    print(f"Generating tags for {target_date}...")
    async with db_manager.get_session() as session:
        stmt = select(StockInfo.code).where(StockInfo.is_active == True)
        result = await session.execute(stmt)
        codes = result.scalars().all()
        
        total = len(codes)
        for i, code in enumerate(codes):
            if i % 100 == 0:
                print(f"Processing tags {i}/{total}...")
                await session.commit() # Commit previous batch
            
            await VolumeAnalysisService.generate_daily_tags(code, target_date, session)
        
        await session.commit()
    print("Tags generation complete.")

async def main():
    service = RuleEngineService(db_manager)
    
    # Calculate for today
    today = date.today()
    
    # Check if today is weekend
    if today.weekday() >= 5:
        today = today - timedelta(days=today.weekday() - 4)

    # 1. Generate Tags
    await generate_tags_for_date(today)
    
    # 2. Calculate Scores
    print(f"Recalculating scores for {today}...")
    result = await service.calculate_daily_scores(today)
    print(f"Result for {today}: {result}")
    
    # Also calculate for yesterday just in case
    yesterday = today - timedelta(days=1)
    if yesterday.weekday() >= 5:
        yesterday = yesterday - timedelta(days=yesterday.weekday() - 4)
        
    # 1. Generate Tags for Yesterday
    await generate_tags_for_date(yesterday)
        
    print(f"Recalculating scores for {yesterday}...")
    result = await service.calculate_daily_scores(yesterday)
    print(f"Result for {yesterday}: {result}")

if __name__ == "__main__":
    asyncio.run(main())
