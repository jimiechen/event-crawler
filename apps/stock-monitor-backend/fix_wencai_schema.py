import sys
import os
import asyncio
from sqlalchemy import text

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import DatabaseManager
from app.config.database import get_config

async def fix_schema():
    print("Initializing database connection...")
    config = get_config()
    db_manager = DatabaseManager(config)
    await db_manager.initialize()
    
    async with db_manager.session_factory() as session:
        print("Checking columns in wencai_crawl_batches...")
        
        # Check query_string
        try:
            # Try to select the column to see if it exists
            await session.execute(text("SELECT query_string FROM wencai_crawl_batches LIMIT 1"))
            print("Column 'query_string' already exists.")
        except Exception as e:
            print(f"Adding column 'query_string'... ({str(e)})")
            # If selection fails, assume column doesn't exist (or table doesn't exist, but we assume table exists)
            try:
                await session.execute(text("ALTER TABLE wencai_crawl_batches ADD COLUMN query_string TEXT COMMENT '原始查询条件'"))
                print("Column 'query_string' added successfully.")
            except Exception as e2:
                print(f"Failed to add 'query_string': {e2}")
            
        # Check tags
        try:
            await session.execute(text("SELECT tags FROM wencai_crawl_batches LIMIT 1"))
            print("Column 'tags' already exists.")
        except Exception as e:
            print(f"Adding column 'tags'... ({str(e)})")
            try:
                await session.execute(text("ALTER TABLE wencai_crawl_batches ADD COLUMN tags JSON COMMENT '解析出的结构化标签'"))
                print("Column 'tags' added successfully.")
            except Exception as e2:
                print(f"Failed to add 'tags': {e2}")
            
        await session.commit()
        print("Schema update completed.")
    
    # Dispose the engine to close connections
    await db_manager.engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_schema())
