import asyncio
import aiohttp
import sys
from sqlalchemy import create_engine, text
from datetime import date

# Configuration
VERIFY_SERVER_URL = "http://localhost:8001/api"
MONITOR_SERVER_URL = "http://localhost:8002" # Trying 8002 as per previous context, will fallback if needed
# But user said 8000 in latest prompt. Let's try 8000 first.
MONITOR_SERVER_URL_8000 = "http://localhost:8000"

DB_URL = "mysql+pymysql://root:12345678@192.168.1.6:3306/stock_monitor_new"

async def call_api(session, url, method="POST", data=None):
    try:
        if method == "POST":
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    print(f"Error calling {url}: {response.status}")
                    text = await response.text()
                    print(text)
                    return None
                return await response.json()
        else:
            async with session.get(url, params=data) as response:
                if response.status != 200:
                    print(f"Error calling {url}: {response.status}")
                    text = await response.text()
                    print(text)
                    return None
                return await response.json()
    except Exception as e:
        print(f"Exception calling {url}: {e}")
        return None

async def main():
    print("Starting verification...")
    
    # 1. Clear All
    async with aiohttp.ClientSession() as session:
        print("1. Clearing all data...")
        res = await call_api(session, f"{VERIFY_SERVER_URL}/clear-all")
        print(f"Clear result: {res}")
        
        # 2. Step 1
        print("2. Running Step 1 (Baseline)...")
        res = await call_api(session, f"{VERIFY_SERVER_URL}/simulation/step1")
        print(f"Step 1 result: {res}")
        
        # 3. Step 2
        print("3. Running Step 2 (2025-11-20)...")
        res = await call_api(session, f"{VERIFY_SERVER_URL}/simulation/step2")
        print(f"Step 2 result: {res}")
        
        # 4. Check DB for future dates
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("4. Checking DB for future dates (> 2025-11-20)...")
            # Check stock_score_result
            result = conn.execute(text("SELECT COUNT(*) FROM stock_score_result WHERE trade_date > '2025-11-20'"))
            count_score = result.scalar()
            print(f"stock_score_result > 2025-11-20 count: {count_score}")
            
            # Check volume_analysis_result
            result = conn.execute(text("SELECT COUNT(*) FROM volume_analysis_result WHERE trade_date > '2025-11-20'"))
            count_vol = result.scalar()
            print(f"volume_analysis_result > 2025-11-20 count: {count_vol}")
            
            # Check if we have 2025-11-20 data
            result = conn.execute(text("SELECT COUNT(*) FROM stock_score_result WHERE trade_date = '2025-11-20'"))
            count_today = result.scalar()
            print(f"stock_score_result = 2025-11-20 count: {count_today}")
            
            if count_score > 0 or count_vol > 0:
                print("FAILED: Future data detected!")
            else:
                print("SUCCESS: No future data detected.")
                
        # 5. Check Dashboard API Performance
        print("5. Checking Ranking API Performance...")
        import time
        start = time.time()
        # Try 8000 first
        url = f"{MONITOR_SERVER_URL_8000}/api/v1/rankings/total?target_date=2025-11-20&limit=100"
        print(f"Calling {url}...")
        res = await call_api(session, url, method="GET")
        if not res:
            # Try 8002
            print("Retrying with port 8002...")
            url = f"{MONITOR_SERVER_URL}/api/v1/rankings/total?target_date=2025-11-20&limit=100"
            res = await call_api(session, url, method="GET")
            
        end = time.time()
        print(f"Ranking API took {end - start:.4f} seconds")
        if res and res.get('success'):
            data = res.get('data', [])
            print(f"Got {len(data)} ranking records")
            if data:
                print(f"Top 1: {data[0]}")
        else:
            print("Ranking API failed")

if __name__ == "__main__":
    asyncio.run(main())
