
import asyncio
import logging
import sys
from app.database import db_manager
from app.services.volume_analysis_service import VolumeAnalysisService
from app.models.stock_daily import StockDaily
from sqlalchemy import select

# Configure logging to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("app.services.volume_analysis_service")
logger.setLevel(logging.INFO)

async def debug_analysis():
    print("Initializing DB...")
    await db_manager.initialize()
    
    code = "002429"
    print(f"Analyzing {code}...")
    
    async with db_manager.get_session() as session:
        # 1. Check data existence manually first
        stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(400)
        result = await session.execute(stmt)
        data = result.scalars().all()
        print(f"Manual check: Found {len(data)} records for {code}")
        if len(data) > 0:
            print(f"Sample data: {data[0].trade_date} - {data[0].close}")
        
        # 2. Run service method
        try:
            # We pass session to reuse the one we opened, or let it create one?
            # The service creates one if None is passed. Let's pass None to simulate API call behavior (if controller uses Depends(get_db_session) it passes one, but let's see)
            # Controller: async def run_analysis(code: str, session: AsyncSession = Depends(get_db_session)):
            # So controller passes a session.
            
            # Let's try passing the session
            result = await VolumeAnalysisService.analyze_stock(code, session=session)
            print("Analysis result:", result)
            
            # 3. Verify DB updates
            from app.models.volume_analysis import StockVolumeBaseline, VolumeAnalysisResult
            
            # Check Baseline
            stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
            baseline = (await session.execute(stmt)).scalars().first()
            print(f"Baseline record: {baseline}")
            if baseline:
                print(f"  3x: {baseline.last_3x_close} on {baseline.last_3x_date}")
                print(f"  Low Vols: {baseline.last_60d_low_vol} on {baseline.last_60d_low_vol_date}")
                
            # Check Results
            stmt = select(VolumeAnalysisResult).where(VolumeAnalysisResult.code == code)
            results = (await session.execute(stmt)).scalars().all()
            print(f"Analysis results count: {len(results)}")
            for r in results[:3]:
                print(f"  {r.trade_date}: {r.analysis_type} - {r.description}")

        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_analysis())
