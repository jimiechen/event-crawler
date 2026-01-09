import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.volume_analysis_service import VolumeAnalysisService
from app.models.stock_daily import StockDaily
from app.models.volume_analysis import VolumeAnalysisResult, StockVolumeBaseline
from sqlalchemy import select

async def reproduce():
    print("Initializing DB...")
    await db_manager.initialize()
    
    code = "002429"
    
    async with db_manager.get_session() as session:
        # 1. Check if daily data exists
        stmt = select(StockDaily).where(StockDaily.code == code).limit(5)
        result = await session.execute(stmt)
        dailies = result.scalars().all()
        
        print(f"Checking daily data for {code}...")
        if not dailies:
            print(f"❌ No daily data found for {code} in stock_daily table!")
            # Check with .SZ suffix
            stmt = select(StockDaily).where(StockDaily.code == f"{code}.SZ").limit(5)
            result = await session.execute(stmt)
            dailies_sz = result.scalars().all()
            if dailies_sz:
                print(f"⚠️ Found data with suffix: {code}.SZ. Code normalization issue?")
            else:
                print("❌ No data found even with suffix.")
        else:
            print(f"✅ Found daily data for {code}. Sample: {dailies[0].trade_date} Close: {dailies[0].close}")

        # 2. Run Analysis
        print(f"\nRunning analysis for {code}...")
        try:
            # analyze_stock returns the baseline dict, NOT anomalies list
            baseline_result = await VolumeAnalysisService.analyze_stock(code, session)
            print(f"Analysis completed. Baseline keys: {list(baseline_result.keys()) if baseline_result else 'None'}")
            
        except Exception as e:
            print(f"❌ Analysis failed with error: {e}")
            import traceback
            traceback.print_exc()
            return

        # 3. Check DB persistence
        print(f"\nChecking persistence for {code}...")
        
        # Check Baseline
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        baseline = (await session.execute(stmt)).scalars().first()
        if baseline:
            print(f"✅ Baseline found: 3x_date={baseline.last_3x_date}, 60d_low={baseline.last_60d_low_vol_date}")
            print(f"   Full Baseline: {baseline.to_dict()}")
        else:
            print("❌ No baseline record found!")

        # Check Results
        stmt = select(VolumeAnalysisResult).where(VolumeAnalysisResult.code == code).order_by(VolumeAnalysisResult.trade_date.desc())
        db_results = (await session.execute(stmt)).scalars().all()
        print(f"✅ Found {len(db_results)} analysis results in DB.")
        for r in db_results[:5]:
             print(f"  - {r.trade_date}: {r.analysis_type} ({r.description})")
        
        # Commit explicit check (though service should have committed)
        # Service commits? Let's check service implementation. 
        # Usually service takes session and lets caller commit, OR commits internally.
        # If I passed a session, I might need to commit if the service didn't.
        # But wait, analyze_stock usually does read-only unless it says save.
        # Ah, analyze_stock docstring or code needs checking. 
        # If it returns results but doesn't save, that's the issue.
        # The controller calls it. Does the controller save?
        
if __name__ == "__main__":
    asyncio.run(reproduce())
