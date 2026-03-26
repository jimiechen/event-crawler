
import asyncio
from app.database import db_manager
from sqlalchemy import text

async def check_tags():
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        # Check stock_info
        print("Checking stock_info for 603992.SH:")
        result = await session.execute(text("SELECT * FROM stock_info WHERE code = '603992.SH'"))
        stock = result.mappings().first()
        print(stock)

        if not stock:
            print("Stock not found in stock_info")
            return

        # Check tags
        print("\nChecking tags for 603992.SH:")
        query = text("""
            SELECT t.id, t.name, t.score
            FROM stock_tags_info t
            JOIN stock_tag_relations st ON t.id = st.tag_id
            WHERE st.stock_code = '603992.SH'
        """)
        result = await session.execute(query)
        tags = result.mappings().all()
        print(f"Found {len(tags)} tags:")
        for tag in tags:
            print(tag)
            
        # Check wencai data logs if possible
        # Check if there is a wencai_stock_info table or similar
        try:
             result = await session.execute(text("SHOW TABLES LIKE 'wencai%'"))
             tables = result.scalars().all()
             print(f"\nWencai tables: {tables}")
             
             if 'wencai_stocks' in tables:
                 print("Checking wencai_stocks for 603992.SH:")
                 # Using stock_code instead of code
                 result = await session.execute(text("SELECT * FROM wencai_stocks WHERE stock_code = '603992.SH' ORDER BY id DESC LIMIT 1"))
                 wencai = result.mappings().first()
                 print(wencai)
                 
                 if wencai:
                     batch_id = wencai['crawl_batch_id']
                     print(f"\nChecking batch {batch_id}:")
                     result = await session.execute(text(f"SELECT * FROM wencai_crawl_batches WHERE id = {batch_id}"))
                     batch = result.mappings().first()
                     print(batch)
                     
                     print(f"\nChecking batch tags relations for batch {batch_id}:")
                     result = await session.execute(text(f"SELECT * FROM batch_tag_relations WHERE batch_id = {batch_id}"))
                     rels = result.mappings().all()
                     print(rels)
        except Exception as e:
            print(f"Error checking wencai tables: {e}")

if __name__ == "__main__":
    asyncio.run(check_tags())
