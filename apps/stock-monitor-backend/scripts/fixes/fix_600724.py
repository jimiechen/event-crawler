import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.volume_analysis_service import VolumeAnalysisService
from app.models.stock import StockInfo
from sqlalchemy import select

async def main():
    code = "600724.SH"
    print(f"Analyzing {code}...")
    
    # Initialize DB
    await db_manager.initialize()
    
    session = db_manager.session_factory()
    try:
        # Check if StockInfo exists, if not create it
        stmt = select(StockInfo).where(StockInfo.code == code)
        result = await session.execute(stmt)
        info = result.scalars().first()
        
        if not info:
            print(f"StockInfo for {code} missing. Creating...")
            info = StockInfo(
                code=code, 
                symbol=code, 
                name="宁波富达", 
                is_active=True
            )
            session.add(info)
            await session.commit()
            print("StockInfo created.")
        else:
            print(f"StockInfo exists: {info.name}")

        # Run analysis
        baseline = await VolumeAnalysisService.analyze_stock(code, session)
        print(f"Analysis complete. Baseline: {baseline}")
        
        # Check Score
        stmt = select(StockInfo).where(StockInfo.code == code)
        result = await session.execute(stmt)
        info = result.scalars().first()
        if info:
            print(f"Stock Info Score: {info.volume_anomaly_score}")
            print(f"Bonus Items: {info.bonus_items}")
        else:
            print("Stock Info not found (Unexpected).")
            
        # Check Baseline Table in DB
        from app.models.volume_analysis import StockVolumeBaseline
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        result = await session.execute(stmt)
        db_baseline = result.scalars().first()
        if db_baseline:
            print(f"DB Baseline: last_3x_date={db_baseline.last_3x_date}, last_3x_close={db_baseline.last_3x_close}")
            print(f"DB Baseline: last_60d_low_vol_date={db_baseline.last_60d_low_vol_date}, val={db_baseline.last_60d_low_vol}")
        else:
            print("DB Baseline not found.")

    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
