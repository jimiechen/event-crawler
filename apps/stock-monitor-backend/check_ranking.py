
import asyncio
import httpx

async def check_ranking_api():
    async with httpx.AsyncClient() as client:
        # Check Total Ranking
        print("Checking Total Ranking...")
        try:
            resp = await client.get("http://localhost:8000/api/v1/rankings/total?limit=10")
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                print(f"Total Ranking Count: {len(data)}")
                for item in data:
                    print(f"  {item['code']} {item['name']}: {item['score']}")
            else:
                print(f"Total Ranking Failed: {resp.status_code}")
        except Exception as e:
            print(f"Total Ranking Error: {e}")

        # Check Growth Ranking
        print("\nChecking Growth Ranking (2025-12-01 to 2025-12-27)...")
        try:
            resp = await client.get("http://localhost:8000/api/v1/rankings/growth?start_date=2025-12-01&end_date=2025-12-27&limit=10")
            if resp.status_code == 200:
                data = resp.json().get('data', [])
                print(f"Growth Ranking Count: {len(data)}")
                for item in data:
                    print(f"  {item['code']} {item['name']}: {item['growth']}")
            else:
                print(f"Growth Ranking Failed: {resp.status_code}")
        except Exception as e:
            print(f"Growth Ranking Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_ranking_api())
