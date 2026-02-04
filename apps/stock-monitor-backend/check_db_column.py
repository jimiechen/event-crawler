import asyncio
from sqlalchemy import text
from app.database import db_manager
from app.config.database import get_config

async def check_and_update_db():
    # Force loading config to ensure db_manager has correct settings
    config = get_config()
    db_manager.config = config
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Check if column exists
        print("Checking if 'is_caw' column exists in 'okooo_matches'...")
        try:
            # This query works for MySQL
            result = await session.execute(text(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_schema = :db_name AND table_name = 'okooo_matches' AND column_name = 'is_caw'"
            ), {"db_name": config.database})
            
            count = result.scalar()
            
            if count == 0:
                print("'is_caw' column missing. Adding it...")
                await session.execute(text(
                    "ALTER TABLE okooo_matches ADD COLUMN is_caw TINYINT DEFAULT 1 COMMENT '是否爬取：1-是，0-否'"
                ))
                await session.commit()
                print("'is_caw' column added successfully.")
            else:
                print("'is_caw' column already exists.")
                
        except Exception as e:
            print(f"Error checking/updating database: {e}")

if __name__ == "__main__":
    # Add parent directory to path so imports work
    import sys
    import os
    sys.path.append(os.getcwd())
    
    asyncio.run(check_and_update_db())
