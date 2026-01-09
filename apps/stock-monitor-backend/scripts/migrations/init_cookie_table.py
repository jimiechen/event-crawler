#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化数据库表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import create_all_tables, init_database, close_database
# 必须导入所有模型，以便SQLAlchemy知道要创建哪些表
from app.models.cookie import ChromeCookie
from app.models.stock import StockInfo

async def main():
    print("Initializing database...")
    await init_database()
    
    print("Creating tables...")
    await create_all_tables()
    
    print("Closing database...")
    await close_database()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
