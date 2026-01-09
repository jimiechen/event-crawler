import asyncio
import logging
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyTasks")

# Add project root to path
sys.path.append("/Users/mac/ok-mcp/app/stock-monitor-backend")

from app.database import db_manager, DatabaseManager
from app.services.tushare_service import TushareService
from app.services.local_data_service import LocalDataService
from app.services.stock_service import StockService
from app.services.rule_engine_service import RuleEngineService

async def verify_tasks():
    logger.info("Starting verification of timed tasks logic...")
    
    # Initialize DB manager
    logger.info("Initializing database...")
    await db_manager.initialize()
    
    # Create a session for services that need it
    async with db_manager.get_session() as session:
        stock_service = StockService(session)
        
        # 1. Test Stock Pool Sync Logic
        # /api/tasks/sync/pool
        logger.info("\n=== Testing Stock Pool Sync Logic ===")
        logger.info("Step 1: Refresh Stock Pool (from MonitorList/Wencai)")
        tushare_service = TushareService(db_manager)
        pool_result = await tushare_service.refresh_stock_pool()
        logger.info(f"Refresh Stock Pool Result: {pool_result}")
        
        logger.info("Step 2: Load Local CSV Data")
        # Note: LocalDataService.load_all_local_data takes stock_service
        # It loads 250 days of data from CSVs in history/daily
        await LocalDataService.load_all_local_data(stock_service)
        logger.info("Local Data Load Completed")
        
        # 2. Test Incremental Sync Logic
        # /api/tasks/sync/incremental
        logger.info("\n=== Testing Incremental Sync Logic ===")
        # mode="incremental" fetches missing data from Tushare for stocks in StockPool
        # It checks get_target_stocks() -> StockPool
        inc_result = await tushare_service.sync_daily_data(mode="incremental")
        logger.info(f"Incremental Sync Result: {inc_result}")
        
        # 3. Test Score Calculation Logic
        # /api/tasks/calculate
        logger.info("\n=== Testing Score Calculation Logic ===")
        rule_service = RuleEngineService(db_manager)
        # Calculate scores for today (or latest available date)
        # If no date provided, it defaults to today or latest
        await rule_service.calculate_daily_scores()
        logger.info("Score Calculation Completed")

    logger.info("\nVerification Finished. Check logs for details.")

if __name__ == "__main__":
    try:
        asyncio.run(verify_tasks())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
