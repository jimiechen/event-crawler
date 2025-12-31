
import asyncio
from app.services.volume_analysis_service import VolumeAnalysisService
from app.database import db_manager
import sys
import os

sys.path.append(os.getcwd())

async def run_analysis():
    async with db_manager.get_session() as session:
        print("Running Volume Analysis for 000881...")
        # Note: analyze_stock creates its own session if not provided, but we can pass one.
        # However, the static method signature is analyze_stock(code, session=None).
        # Let's pass the session to reuse connection, but need to be careful about commits.
        # VolumeAnalysisService.analyze_stock commits internally.
        
        await VolumeAnalysisService.analyze_stock("000881", session=session)
        print("Analysis complete.")

if __name__ == "__main__":
    asyncio.run(run_analysis())
