#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Drop all tables to reset database
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.database_pool import DatabasePool
from app.config.database import DatabaseConfig

async def drop_tables():
    print("Dropping tables...")
    
    tables = [
        "monitor_stats", # View
        "latest_stock_data", # View
        "monitor_list",
        "stock_data",
        "stock_info",
        "data_dedup_log",
        "system_config",
        "analysis_logs",
        "volume_price_logs",
        "wencai_stocks",
        "wencai_crawl_batches",
        "wencai_data_dedup",
        "v_latest_wencai_stocks", # View
        "v_wencai_crawl_stats" # View
    ]
    
    try:
        db_pool = DatabasePool(DatabaseConfig())
        await db_pool.initialize()
        
        for table in tables:
            try:
                # Check if view or table
                await db_pool.execute_update(f"DROP VIEW IF EXISTS {table}")
                await db_pool.execute_update(f"DROP TABLE IF EXISTS {table}")
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Failed to drop {table}: {e}")
        
        await db_pool.close()
        print("Tables dropped.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(drop_tables())
