import asyncio
import aiohttp
import sys

async def test_api():
    async with aiohttp.ClientSession() as session:
        try:
            # Test getting stocks with new params
            url = "http://localhost:8000/api/v1/dashboard/stocks"
            params = {
                "page": 1,
                "page_size": 10,
                "sort_by": "volume_anomaly_score",
                "sort_order": "desc"
            }
            async with session.get(url, params=params) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print("Success!")
                    if data['data']['items']:
                        item = data['data']['items'][0]
                        print("Sample Item Keys:", item.keys())
                        # Check for new keys
                        expected_keys = ['latest_price', 'volume_anomaly_score', 'bonus_items', 'sync_incremental']
                        missing = [k for k in expected_keys if k not in item]
                        if missing:
                            print(f"Missing keys: {missing}")
                        else:
                            print("All new keys present.")
                    else:
                        print("No items returned (DB might be empty of stocks or no active ones).")
                else:
                    print(await resp.text())
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())