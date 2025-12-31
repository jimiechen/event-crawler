#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock import StockInfo
from sqlalchemy import update

async def main():
    print("Connecting to database...")
    async with db_manager.get_session() as session:
        print("Updating market field to empty string...")
        stmt = update(StockInfo).values(market="")
        result = await session.execute(stmt)
        await session.commit()
        print(f"Updated {result.rowcount} records.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
