import asyncio
from sqlalchemy import text
from app.database import get_db_session

async def check_schema():
    async for session in get_db_session():
        try:
            print("Checking schema...")
            # Check tonghuashun_stocks schema
            print("\n=== Schema of tonghuashun_stocks ===")
            try:
                result = await session.execute(text("DESCRIBE tonghuashun_stocks"))
                for row in result:
                    print(row)
            except Exception as e:
                print(f"tonghuashun_stocks error: {e}")

            # Check tonghuashun_raw_logs schema
            print("\n=== Schema of tonghuashun_raw_logs ===")
            try:
                result = await session.execute(text("DESCRIBE tonghuashun_raw_logs"))
                for row in result:
                    print(row)
            except Exception as e:
                print(f"tonghuashun_raw_logs error: {e}")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await session.close()
            break

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(check_schema())
