#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化定时任务系统数据库表
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import DatabaseManager
from app.models.base import Base
# 导入所有模型以确保它们被注册到Base.metadata
from app.models import *

async def main():
    logger.info("开始初始化定时任务系统数据库表...")
    
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    if not db_manager.engine:
        logger.error("数据库连接失败")
        return
        
    try:
        async with db_manager.engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("数据库表初始化成功！")
        
    except Exception as e:
        logger.error(f"数据库表初始化失败: {e}")
        
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
