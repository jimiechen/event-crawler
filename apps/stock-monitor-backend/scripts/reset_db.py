import asyncio
import sys
import os
from sqlalchemy import text

# Ensure app is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import db_manager

async def reset_db():
    tables = [
        "wencai_stocks",
        "monitor_list",
        "stock_info",
        "stock_daily",
        "stock_daily_temp",
        "stock_volume_baseline",
        "stock_tag_relations",
        "stock_score_results",
        "volume_analysis_results",
        "alert_records",
        "wencai_data_dedup",
        "stock_concepts"
    ]
    
    print("Resetting database...")
    try:
        async with db_manager.get_session() as session:
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            for table in tables:
                try:
                    await session.execute(text(f"TRUNCATE TABLE {table}"))
                    print(f"Truncated {table}")
                except Exception as e:
                    # Ignore table not exists
                    print(f"Failed to truncate {table}: {e}")
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            await session.commit()
    finally:
        await db_manager.close()
    
    print("Database reset complete.")

if __name__ == "__main__":
    asyncio.run(reset_db())
