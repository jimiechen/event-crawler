#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import DatabaseManager

async def test_db():
    db = DatabaseManager()
    await db.initialize()
    print('Database connection successful')
    await db.close()

if __name__ == '__main__':
    asyncio.run(test_db())
