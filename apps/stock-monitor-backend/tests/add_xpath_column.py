import asyncio
import sys
import os

# Add parent dir to path so we can import app
current_dir = os.path.dirname(os.path.abspath(__file__))
# app is inside stock-monitor-backend
sys.path.append(current_dir)

from app.database import DatabaseManager
from sqlalchemy import text

async def add_column():
    print("Initializing database connection...")
    db = DatabaseManager()
    await db.initialize()
    
    async with db.engine.connect() as conn:
        try:
            print("Attempting to add xpath_config column to crawler_targets...")
            await conn.execute(text("ALTER TABLE crawler_targets ADD COLUMN xpath_config TEXT COMMENT 'XPath配置(JSON)';"))
            await conn.commit()
            print("Successfully added xpath_config column.")
        except Exception as e:
            print(f"Error adding column (might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(add_column())
