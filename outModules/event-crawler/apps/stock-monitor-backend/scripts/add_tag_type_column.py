import asyncio
import os
import sys
from sqlalchemy import text

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import DatabaseManager

async def main():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        try:
            print("Checking if tag_type column exists in stock_tags_info...")
            # Check if column exists
            result = await session.execute(text("SHOW COLUMNS FROM stock_tags_info LIKE 'tag_type'"))
            if result.fetchone():
                print("Column 'tag_type' already exists.")
            else:
                print("Adding 'tag_type' column to stock_tags_info...")
                await session.execute(text("ALTER TABLE stock_tags_info ADD COLUMN tag_type VARCHAR(20) DEFAULT 'calculation' COMMENT '标签类型(date/calculation)'"))
                await session.commit()
                print("Column 'tag_type' added successfully.")
            
            # Optional: Try to identify date tags and update them
            # Assuming date tags might be in format 'YYYY-MM-DD' or 'YYYYMMDD'
            print("Attempting to identify and update existing date tags...")
            
            # Find tags that look like dates (YYYY-MM-DD)
            date_regex = r'^\d{4}-\d{2}-\d{2}$'
            # MySQL regex syntax might vary, using simple LIKE for common formats
            # Update tags that match date pattern
            
            # Simple heuristic: tags starting with 202 and length 10 (202x-xx-xx) or 8 (202xxxxx)
            sql_update = """
            UPDATE stock_tags_info 
            SET tag_type = 'date' 
            WHERE (name REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' OR name REGEXP '^[0-9]{8}$')
            """
            
            # Check if REGEXP is supported (MySQL yes, SQLite no)
            # Since environment is likely MySQL, we try. If fails, we catch.
            try:
                await session.execute(text(sql_update))
                await session.commit()
                print("Updated potential date tags to type 'date'.")
            except Exception as e:
                print(f"Could not auto-update date tags (might be SQLite or syntax error): {e}")
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
