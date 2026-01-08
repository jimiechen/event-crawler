
import asyncio
import sys
import os
from sqlalchemy import text
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'app'))

from app.database import db_manager

async def get_queries():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        # Check trading dates
        try:
            stmt = text("SELECT DISTINCT trade_date FROM stock_daily WHERE trade_date BETWEEN '2025-11-20' AND '2025-12-10' ORDER BY trade_date")
            result = await session.execute(stmt)
            rows = result.fetchall()
            print(f"Found {len(rows)} trading dates.")
            for row in rows:
                print(f"DATE|{row.trade_date}")
        except Exception as e:
            print(f"Error checking dates: {e}")

        # Check if any query strings exist
        try:
            stmt = text("SELECT id, query_string, started_at FROM wencai_crawl_batches WHERE query_string IS NOT NULL LIMIT 5")
            result = await session.execute(stmt)
            rows = result.fetchall()
            print(f"Found {len(rows)} batches with query strings.")
            for row in rows:
                print(f"BATCH_WITH_QUERY|{row.id}|{row.started_at}|{row.query_string}")
        except Exception as e:
            print(f"Error checking queries: {e}")

if __name__ == "__main__":
    asyncio.run(get_queries())
