import asyncio
import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.getcwd())

from app.database import db_manager
from sqlalchemy import text

async def main():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        # Check if column exists (MySQL specific)
        try:
            # Try to select the column to see if it exists
            await session.execute(text("SELECT is_caw FROM okooo_matches LIMIT 1"))
            print("Column 'is_caw' already exists.")
        except Exception:
            print("Column 'is_caw' does not exist. Adding it...")
            try:
                await session.execute(text("ALTER TABLE okooo_matches ADD COLUMN is_caw INT DEFAULT 1 COMMENT '是否爬取：1-是，0-否'"))
                await session.commit()
                print("Column 'is_caw' added successfully.")
            except Exception as e:
                print(f"Failed to add column: {e}")

if __name__ == "__main__":
    asyncio.run(main())
