#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 wencai_crawl_batches 表的 status 字段长度
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.database import db_manager
from sqlalchemy import text

async def fix_status_column():
    """修复 status 字段长度"""
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # 修改 status 字段长度为 50
        sql = "ALTER TABLE wencai_crawl_batches MODIFY COLUMN status VARCHAR(50) DEFAULT 'pending'"
        await session.execute(text(sql))
        await session.commit()
        print("✅ 修复完成: status 字段长度已修改为 VARCHAR(50)")

if __name__ == "__main__":
    asyncio.run(fix_status_column())
