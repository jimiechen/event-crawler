import asyncio
import logging
from sqlalchemy import text
from app.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_tags():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        logger.info("--- Debugging Tags for 603992.SH ---")
        
        # 1. Check all relations for 603992.SH
        logger.info("Querying stock_tag_relations for 603992.SH...")
        relations_sql = text("SELECT * FROM stock_tag_relations WHERE stock_code = '603992.SH'")
        result = await session.execute(relations_sql)
        relations = result.fetchall()
        for r in relations:
            logger.info(f"Relation: {r}")
            
        # 2. Check details of referenced tags
        tag_ids = [r.tag_id for r in relations]
        if tag_ids:
            logger.info(f"Querying stock_tags_info details for IDs: {tag_ids}...")
            # Handle single item tuple syntax in SQL IN clause
            if len(tag_ids) == 1:
                tags_sql = text(f"SELECT * FROM stock_tags_info WHERE id = {tag_ids[0]}")
            else:
                tags_sql = text(f"SELECT * FROM stock_tags_info WHERE id IN {tuple(tag_ids)}")
            
            result = await session.execute(tags_sql)
            tags = result.fetchall()
            for t in tags:
                logger.info(f"Tag: {t}")
        else:
            logger.info("No relations found.")

        # 3. Check specifically for Tag ID 42 and 32 (from previous logs)
        logger.info("--- Checking specific Tag IDs 32 and 42 ---")
        specific_tags_sql = text("SELECT * FROM stock_tags_info WHERE id IN (32, 42)")
        result = await session.execute(specific_tags_sql)
        specific_tags = result.fetchall()
        for t in specific_tags:
            logger.info(f"Specific Tag: {t}")

        # 4. Check if relation exists for 32 or 42
        logger.info("--- Checking relations for 32 and 42 ---")
        specific_rels_sql = text("SELECT * FROM stock_tag_relations WHERE stock_code = '603992.SH' AND tag_id IN (32, 42)")
        result = await session.execute(specific_rels_sql)
        specific_rels = result.fetchall()
        for r in specific_rels:
            logger.info(f"Specific Relation: {r}")

if __name__ == "__main__":
    asyncio.run(debug_tags())
