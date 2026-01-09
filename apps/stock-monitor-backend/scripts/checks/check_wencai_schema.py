import asyncio
from sqlalchemy import text
from app.database import get_db_session

async def check_schema():
    async for session in get_db_session():
        try:
            print("Checking wencai_stocks schema...")
            result = await session.execute(text("DESCRIBE wencai_stocks"))
            rows = result.fetchall()
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await session.close()
            break

if __name__ == "__main__":
    asyncio.run(check_schema())
