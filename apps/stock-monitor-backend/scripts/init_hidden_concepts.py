import asyncio
import sys
import os

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models.stock import HiddenConcept
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    print("Initializing database connection...")
    await db_manager.initialize()
    print("Initializing HiddenConcept table...")
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(HiddenConcept.metadata.create_all)
    print("HiddenConcept table initialized.")

if __name__ == "__main__":
    asyncio.run(main())
