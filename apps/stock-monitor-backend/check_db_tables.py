import asyncio
from sqlalchemy import text
from app.database import get_db_session

async def check_tables():
    async for session in get_db_session():
        try:
            print("Checking tables...")
            # Check tonghuashun_stocks
            result = await session.execute(text("DESCRIBE tonghuashun_stocks"))
            print("\nTable: tonghuashun_stocks")
            for row in result:
                print(row)
            
            # Check tonghuashun_raw_logs
            result = await session.execute(text("DESCRIBE tonghuashun_raw_logs"))
            print("\nTable: tonghuashun_raw_logs")
            for row in result:
                print(row)
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await session.close()
            break

if __name__ == "__main__":
    import sys
    import os
    # Add project root to path
    sys.path.append(os.getcwd())
    asyncio.run(check_tables())
