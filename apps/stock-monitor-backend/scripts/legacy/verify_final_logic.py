
import asyncio
import logging
import sys
import os
from datetime import date, timedelta
from httpx import AsyncClient

# Add project root to path
sys.path.append("/Users/mac/ok-mcp/app/stock-monitor-backend")

from app.main import app
from app.database import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyFinal")

async def test_ranking_api(client):
    logger.info("\n=== Testing Ranking API ===")
    
    # 1. Growth Ranking
    today = date.today()
    yesterday = today - timedelta(days=1)
    # Ensure we use string format YYYY-MM-DD
    start_date = yesterday.isoformat()
    end_date = today.isoformat()
    
    logger.info(f"Testing Growth Ranking with start={start_date}, end={end_date}")
    response = await client.get("/api/v1/rankings/growth", params={
        "start_date": start_date,
        "end_date": end_date,
        "limit": 10
    })
    
    if response.status_code == 200:
        logger.info("✅ Growth Ranking API Success")
        data = response.json()
        logger.info(f"Data count: {len(data.get('data', []))}")
    else:
        logger.error(f"❌ Growth Ranking API Failed: {response.status_code} - {response.text}")

    # 2. Total Ranking
    logger.info(f"Testing Total Ranking with target={end_date}")
    response = await client.get("/api/v1/rankings/total", params={
        "target_date": end_date,
        "limit": 10
    })
    
    if response.status_code == 200:
        logger.info("✅ Total Ranking API Success")
        data = response.json()
        logger.info(f"Data count: {len(data.get('data', []))}")
    else:
        logger.error(f"❌ Total Ranking API Failed: {response.status_code} - {response.text}")

async def test_timed_task_apis(client):
    logger.info("\n=== Testing Timed Task APIs ===")
    
    # 1. Rules check
    response = await client.get("/api/tasks/rules")
    if response.status_code == 200:
        logger.info("✅ Task Router is mounted correctly")
    else:
        logger.error(f"❌ Task Router not mounted: {response.status_code}")

    # 2. Pool Sync: /api/tasks/sync/pool
    logger.info("Testing Pool Sync Endpoint...")
    # This might trigger a long running task.
    # In real app, this is async, but here we await the response which awaits the handler.
    # The handler awaits TushareService.refresh_stock_pool().
    
    try:
        response = await client.post("/api/tasks/sync/pool", timeout=60.0)
        if response.status_code == 200:
            logger.info("✅ Pool Sync API Success")
            logger.info(f"Response: {response.json()}")
        else:
            logger.error(f"❌ Pool Sync API Failed: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Pool Sync API Exception: {e}")

    # 3. Incremental Sync
    logger.info("Testing Incremental Sync Endpoint...")
    try:
        response = await client.post("/api/tasks/sync/incremental", timeout=60.0)
        if response.status_code == 200:
            logger.info("✅ Incremental Sync API Success")
            logger.info(f"Response: {response.json()}")
        else:
            logger.error(f"❌ Incremental Sync API Failed: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Incremental Sync API Exception: {e}")

    # 4. Calculate
    logger.info("Testing Calculate Endpoint...")
    try:
        response = await client.post("/api/tasks/calculate", timeout=60.0)
        if response.status_code == 200:
            logger.info("✅ Calculate API Success")
            logger.info(f"Response: {response.json()}")
        else:
            logger.error(f"❌ Calculate API Failed: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Calculate API Exception: {e}")

async def main():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # We need to manually trigger startup event if AsyncClient doesn't do it automatically in the way we want?
        # AsyncClient(app=app) uses ASGI app directly. 
        # For lifespan support, we might need LifespanManager or just let httpx handle it (it usually does if app is ASGI).
        # Actually httpx AsyncClient with app argument sends requests to the app. 
        # But to ensure startup events run (db init), we usually use a context manager or lifespan context.
        # However, for simplicity, let's assume app's on_event("startup") or lifespan works.
        # FastAPI's lifespan is context manager.
        
        # We can use `async with lifespan(app):` but lifespan is defined in main.py.
        # Let's import it if needed.
        pass
        
        # Run tests
        await test_ranking_api(client)
        await test_timed_task_apis(client)

if __name__ == "__main__":
    asyncio.run(main())
    logger.info("Testing Incremental Sync Endpoint...")
    # Note: This might fail if Tushare token is invalid or network is down, but we test the endpoint reachability.
    response = client.post("/api/tasks/sync/incremental")
    if response.status_code == 200:
        logger.info("✅ Incremental Sync API Success")
        logger.info(f"Response: {response.json()}")
    else:
        # It might return 200 with "failed" status in body if logic fails, or 500 if exception.
        logger.info(f"ℹ️ Incremental Sync API Result: {response.status_code} - {response.text}")

    # 3. Calculate: /api/tasks/calculate
    logger.info("Testing Score Calculation Endpoint...")
    response = client.post("/api/tasks/calculate")
    if response.status_code == 200:
        logger.info("✅ Score Calculation API Success")
        logger.info(f"Response: {response.json()}")
    else:
        logger.error(f"❌ Score Calculation API Failed: {response.status_code} - {response.text}")

async def main():
    # Initialize DB for the app within TestClient context if needed?
    # TestClient starts the app. The app lifespan event initializes DB.
    # So we don't need manual init if using TestClient.
    
    # However, TestClient uses requests (sync).
    # App is async.
    
    test_ranking_api()
    test_timed_task_apis()

if __name__ == "__main__":
    # We don't need asyncio.run for TestClient calls as they are sync.
    # But if we wanted to call services directly we would.
    # Here we stick to TestClient.
    try:
        test_ranking_api()
        test_timed_task_apis()
    except Exception as e:
        logger.error(f"Test Failed: {e}")
