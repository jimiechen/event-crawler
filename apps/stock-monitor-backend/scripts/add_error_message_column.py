import sys
import os
import asyncio
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager

async def add_column():
    print("Initializing database connection...")
    await db_manager.initialize()
    
    print("Checking if column exists...")
    async with db_manager.get_session() as session:
        try:
            # Check if column exists
            result = await session.execute(text(
                "SELECT count(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'generic_tasks' "
                "AND COLUMN_NAME = 'error_message'"
            ))
            exists = result.scalar()
            
            if exists:
                print("Column 'error_message' already exists.")
            else:
                print("Adding column 'error_message'...")
                await session.execute(text(
                    "ALTER TABLE generic_tasks ADD COLUMN error_message TEXT COMMENT '最后一次错误信息'"
                ))
                print("Column added successfully.")
                
        except Exception as e:
            print(f"Error: {e}")
            raise
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(add_column())
