import asyncio
import sys
import os

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scheduler_service import scheduler_service
from app.database import db_manager

async def test_ai_review():
    print("Initializing DB...")
    await db_manager.initialize()
    
    print("Running AI review task...")
    await scheduler_service.run_daily_ai_review()
    
    print("Done.")

if __name__ == "__main__":
    asyncio.run(test_ai_review())
