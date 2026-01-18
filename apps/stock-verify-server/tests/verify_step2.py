import asyncio
import aiohttp
import json

async def test_simulation():
    url = "http://localhost:8002/api/simulation/step2"
    payload = {
        "stock_code": "603601",
        "start_date": "2024-02-01",
        "end_date": "2024-02-20"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            print(f"Status: {response.status}")
            text = await response.text()
            print(f"Response: {text}")

if __name__ == "__main__":
    asyncio.run(test_simulation())
