import asyncio
from sqlalchemy import text
from app.database import db_manager

async def add_tags_column():
    print("Starting database schema update...")
    try:
        await db_manager.initialize()
        
        async with db_manager.session_factory() as session:
            print("Checking if tags column exists in wencai_crawl_batches...")
            try:
                # Try to select tags column to see if it exists
                await session.execute(text("SELECT tags FROM wencai_crawl_batches LIMIT 1"))
                print("Column 'tags' already exists.")
            except Exception:
                print("Column 'tags' does not exist. Adding it...")
                # Add tags column as JSON type (or TEXT if JSON not supported, but assuming MySQL 5.7+)
                # Using JSON type for better structured data storage
                await session.execute(text("ALTER TABLE wencai_crawl_batches ADD COLUMN tags JSON COMMENT '批次关联的标签列表'"))
                await session.commit()
                print("Column 'tags' added successfully.")

    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == "__main__":
    asyncio.run(add_tags_column())
