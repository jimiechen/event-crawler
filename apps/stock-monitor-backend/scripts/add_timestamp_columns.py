#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 updated_at 和 created_at 字段到 wencai_crawl_batches 表
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.database import db_manager
from sqlalchemy import text

async def add_timestamp_columns():
    """添加时间戳字段"""
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # 检查 created_at 字段是否存在
        check_sql = """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = DATABASE()
        AND table_name = 'wencai_crawl_batches' 
        AND column_name = 'created_at'
        """
        result = await session.execute(text(check_sql))
        if result.scalar() == 0:
            # 添加 created_at 字段
            sql = """
            ALTER TABLE wencai_crawl_batches 
            ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            """
            await session.execute(text(sql))
            print("✅ 添加 created_at 字段")
        else:
            print("⚠️ created_at 字段已存在")
        
        # 检查 updated_at 字段是否存在
        check_sql = """
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_schema = DATABASE()
        AND table_name = 'wencai_crawl_batches' 
        AND column_name = 'updated_at'
        """
        result = await session.execute(text(check_sql))
        if result.scalar() == 0:
            # 添加 updated_at 字段
            sql = """
            ALTER TABLE wencai_crawl_batches 
            ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            """
            await session.execute(text(sql))
            print("✅ 添加 updated_at 字段")
        else:
            print("⚠️ updated_at 字段已存在")
        
        await session.commit()
        print("✅ 修复完成")

if __name__ == "__main__":
    asyncio.run(add_timestamp_columns())
