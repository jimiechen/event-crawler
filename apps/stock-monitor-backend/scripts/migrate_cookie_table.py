#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate chrome_cookies table to add new fields
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager

async def migrate():
    print("Initializing database...")
    await db_manager.initialize()
    
    print("Migrating chrome_cookies table...")
    async with db_manager.get_session() as session:
        # Check if columns exist
        try:
            # We use raw SQL to check and alter table because SQLAlchemy create_all doesn't handle migrations
            
            # List of new columns to add
            # (column_name, column_definition)
            new_columns = [
                ("account_name", "VARCHAR(100) COMMENT '账号名称/备注'"),
                ("test_url", "TEXT COMMENT '测试URL'"),
                ("xpath_config", "TEXT COMMENT 'XPath配置(JSON)'"),
                ("status", "VARCHAR(20) DEFAULT 'unknown' COMMENT '状态: active, expired, unknown'"),
                ("last_checked_at", "DATETIME COMMENT '上次检查时间'"),
                ("is_valid", "BOOLEAN DEFAULT TRUE COMMENT 'Cookie是否有效'")
            ]
            
            for col_name, col_def in new_columns:
                try:
                    # Check if column exists
                    # This query is specific to MySQL, which seems to be what is used based on search results
                    check_sql = text(f"SHOW COLUMNS FROM chrome_cookies LIKE '{col_name}'")
                    result = await session.execute(check_sql)
                    if not result.fetchone():
                        print(f"Adding column {col_name}...")
                        alter_sql = text(f"ALTER TABLE chrome_cookies ADD COLUMN {col_name} {col_def}")
                        await session.execute(alter_sql)
                        print(f"Column {col_name} added.")
                    else:
                        print(f"Column {col_name} already exists.")
                except Exception as e:
                    print(f"Error processing column {col_name}: {e}")
            
            await session.commit()
            print("Migration completed successfully.")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            await session.rollback()
    
    # Close database connection (if needed by the manager)
    # db_manager doesn't have a close method exposed directly usually, but let's check if we need to do anything.
    # The session context manager handles session closing.
    
if __name__ == "__main__":
    asyncio.run(migrate())
