#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
from pathlib import Path
from loguru import logger
from sqlalchemy import text

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import DatabaseManager

async def main():
    logger.info("Adding stock_code column to task_execution_log...")
    
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    if not db_manager.engine:
        logger.error("Database connection failed")
        return
        
    try:
        async with db_manager.engine.begin() as conn:
            # Check if column exists (simple way: try to add it and ignore error, or check schema)
            # MySQL syntax
            try:
                await conn.execute(text("ALTER TABLE task_execution_log ADD COLUMN stock_code VARCHAR(20) NULL COMMENT '股票代码(可选)'"))
                logger.info("Column stock_code added successfully.")
            except Exception as e:
                logger.warning(f"Failed to add column (maybe exists?): {e}")
            
    except Exception as e:
        logger.error(f"Error executing migration: {e}")
        
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
