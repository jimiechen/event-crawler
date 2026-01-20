
import httpx
import asyncio
import json

async def test_step2():
    # url = "http://localhost:8001/api/simulation/step2"
    # url = "http://localhost:8001/api/simulation/run/2025-11-21"
    url = "http://localhost:8001/api/simulation/run/2025-11-24"
    print(f"Connecting to {url}...")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", url) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            msg_type = data.get("type")
                            message = data.get("message")
                            
                            print(f"[{msg_type}] {message}")
                            
                            if "获取到" in message and "只累计股票" in message:
                                print("SUCCESS: Verified cumulative stock fetching!")
                            
                            if msg_type == "success" and "每日模拟执行完成" in message:
                                print("Simulation Completed.")
                                break
                            
                            if msg_type == "error":
                                print("ERROR detected!")
                                break
                                
                        except json.JSONDecodeError:
                            print(f"Raw data: {data_str}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_step2())
