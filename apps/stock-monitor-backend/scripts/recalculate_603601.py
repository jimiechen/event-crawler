import asyncio
import os
import sys
from datetime import date
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock_daily import StockScoreResult
from app.services.volume_analysis_service import VolumeAnalysisService
from sqlalchemy import delete

async def recalculate_603601():
    print("🚀 Recalculating scores for 603601...")
    
    await db_manager.initialize()
    stock_code = "603601"
    
    # 1. Clear existing scores
    print("Cleaning up existing scores...")
    async with db_manager.get_session() as session:
        stmt = delete(StockScoreResult).where(StockScoreResult.code == stock_code)
        await session.execute(stmt)
        await session.commit()
    
    # 2. Trigger Analysis
    print("Triggering volume analysis...")
    try:
        await VolumeAnalysisService.analyze_stock(stock_code)
        print("✅ Analysis completed successfully.")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(recalculate_603601())
    except KeyboardInterrupt:
        pass
