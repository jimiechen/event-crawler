import asyncio
from sqlalchemy import text
from app.database import get_db_session
import json
from decimal import Decimal
from datetime import date, datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DateTimeEncoder, self).default(obj)

async def check_data():
    async for session in get_db_session():
        try:
            print("Checking latest data...")
            
            # Check tonghuashun_stocks
            print("\n=== Latest 5 records in tonghuashun_stocks ===")
            result = await session.execute(text("SELECT id, code, name, current_price, timestamp, created_at FROM tonghuashun_stocks ORDER BY id DESC LIMIT 5"))
            rows = result.fetchall()
            if not rows:
                print("No data found in tonghuashun_stocks")
            else:
                for row in rows:
                    print(row)
            
            # Check tonghuashun_raw_logs
            print("\n=== Latest 5 records in tonghuashun_raw_logs ===")
            result = await session.execute(text("SELECT id, source, request_timestamp, created_at, parse_status FROM tonghuashun_raw_logs ORDER BY id DESC LIMIT 5"))
            rows = result.fetchall()
            if not rows:
                print("No data found in tonghuashun_raw_logs")
            else:
                for row in rows:
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
    asyncio.run(check_data())
