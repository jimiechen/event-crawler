
import asyncio
from sqlalchemy import text
from app.database import get_db_session

async def check_concepts():
    async for session in get_db_session():
        try:
            # Check concept format in DB
            result = await session.execute(text(
                "SELECT concept FROM wencai_stocks WHERE concept IS NOT NULL LIMIT 5"
            ))
            rows = result.fetchall()
            print("Concept samples:")
            for row in rows:
                print(row[0])
                
            # Count total
            result = await session.execute(text("SELECT COUNT(*) FROM wencai_stocks"))
            count = result.scalar()
            print(f"Total stocks: {count}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await session.close()
            break

if __name__ == "__main__":
    asyncio.run(check_concepts())
