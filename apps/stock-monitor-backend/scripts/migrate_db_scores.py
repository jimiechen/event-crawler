
import asyncio
from sqlalchemy import text
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager

async def upgrade_db():
    print("Starting DB migration...")
    async with db_manager.get_session() as session:
        # Check if columns exist
        try:
            await session.execute(text("ALTER TABLE stock_score_result ADD COLUMN daily_score DECIMAL(10, 2) DEFAULT 0 COMMENT '每日得分'"))
            print("Added daily_score column")
        except Exception as e:
            print(f"daily_score might exist: {e}")
            
        try:
            await session.execute(text("ALTER TABLE stock_score_result ADD COLUMN accumulated_score DECIMAL(10, 2) DEFAULT 0 COMMENT '累计得分'"))
            print("Added accumulated_score column")
        except Exception as e:
            print(f"accumulated_score might exist: {e}")
            
        # Also update total_score comment if possible (might not work on all DBs easily, skip for now or try)
        try:
            # MySQL syntax
            await session.execute(text("ALTER TABLE stock_score_result MODIFY COLUMN total_score DECIMAL(10, 2) DEFAULT 0 COMMENT '总分(兼容字段，同accumulated_score)'"))
            print("Updated total_score comment")
        except Exception as e:
            print(f"Could not update total_score comment (non-critical): {e}")
        
        await session.commit()
    print("Migration finished.")

if __name__ == "__main__":
    asyncio.run(upgrade_db())
