
import asyncio
import httpx
import sys

async def test_api():
    url = "http://localhost:8000/api/v1/test-tool/add-custom-stock"
    payload = {
        "code": "002735",
        "label": "Test",
        "platform": "tushare"
    }
    
    print(f"Sending request to {url}...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                daily_data = data.get("daily_data", [])
                print(f"Daily Data Count: {len(daily_data)}")
                if daily_data:
                    last_item = daily_data[-1]
                    print(f"Last Item: {last_item}")
                    print(f"Last Close: {last_item.get('close')}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
