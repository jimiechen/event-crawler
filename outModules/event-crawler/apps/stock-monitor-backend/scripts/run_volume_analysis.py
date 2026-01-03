import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.services.volume_analysis_service import VolumeAnalysisService
from loguru import logger

async def main():
    logger.info("Initializing database...")
    await db_manager.initialize()
    
    logger.info("Starting full volume analysis...")
    await VolumeAnalysisService.analyze_all_stocks(batch_size=50)
    
    logger.info("Analysis completed.")

if __name__ == "__main__":
    asyncio.run(main())
