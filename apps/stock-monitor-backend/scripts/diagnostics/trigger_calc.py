
import asyncio
import httpx
from sqlalchemy import select
from app.database import db_manager
from app.models.stock import StockInfo

async def trigger_recalculation():
    await db_manager.initialize()
    async with db_manager.get_session() as db:
        # Get all active stocks
        query = select(StockInfo.code).limit(20) # Test with 20 first
        result = await db.execute(query)
        codes = result.scalars().all()
        
        print(f"Triggering calculation for {len(codes)} stocks...")
        
        async with httpx.AsyncClient() as client:
            for code in codes:
                try:
                    url = f"http://localhost:8000/api/v1/volume-analysis/run/{code}"
                    resp = await client.get(url, timeout=10)
                    print(f"  {code}: {resp.status_code} - {resp.json().get('message', 'No msg')}")
                except Exception as e:
                    print(f"  {code}: Error {e}")

if __name__ == "__main__":
    asyncio.run(trigger_recalculation())
