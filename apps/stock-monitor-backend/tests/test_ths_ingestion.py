import asyncio
import aiohttp
import json
import time

async def send_test_request():
    url = "http://localhost:8000/api/v1/stocks/tonghuashun/raw-data"
    payload = {
        "source": "test_script",
        "data": [
            {
                "url": "http://test.url",
                "requestId": f"test_req_{int(time.time())}",
                "timestamp": str(int(time.time())),
                "hs": {
                    "300466": {
                        "6": "9.65",
                        "7": "9.61", 
                        "8": "9.67",
                        "9": "9.40",
                        "10": "9.40",
                        "13": "7199100.00",
                        "19": "68172919.00",
                        "199112": "-2.591",
                        "264648": "-0.250",
                        "526792": "2.798",
                        "1968584": "1.604",
                        "2034120": "",
                        "3541450": "5033981100.000",
                        "name": "赛摩智能"
                    }
                }
            }
        ]
    }
    
    print(f"Sending request to {url}...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                print(f"Status: {response.status}")
                print(f"Response: {await response.text()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_request())
