
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import DatabaseManager
from app.models.stock import WencaiStock
from sqlalchemy import select, func

async def check_wencai_count():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        result = await session.execute(select(func.count()).select_from(WencaiStock))
        count = result.scalar()
        print(f"Wencai Stock Count: {count}")

if __name__ == "__main__":
    asyncio.run(check_wencai_count())
