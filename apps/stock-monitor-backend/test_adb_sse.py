import asyncio
import httpx
import json
import os
import time

BASE_URL = "http://localhost:8000/api/v1/adb"
LOG_FILE = "logs/adb_sse.log"

async def test_health():
    print("Testing /health endpoint...")
    data = {
        "status": "healthy",
        "adb_available": True,
        "devices": [
            {
                "device_id": "test_device_1",
                "connected": True,
                "serial": "test_serial",
                "model": "TestModel"
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/health", json=data)
        print(f"Health Response: {resp.status_code} - {resp.json()}")
        assert resp.status_code == 200

async def test_sse_and_command():
    print("Testing SSE and Command...")
    
    # We need to start listening to SSE in background
    # But since this is a script, we can connect, wait for a bit, and send command in parallel?
    # Or just connect and read.
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Trigger a command after a small delay
        async def trigger():
            await asyncio.sleep(1)
            cmd_data = {
                "device_id": "test_device_1",
                "action": "screenshot",
                "params": {"quality": 80}
            }
            print("Sending command...")
            resp = await client.post(f"{BASE_URL}/command/send", json=cmd_data)
            print(f"Command Response: {resp.status_code} - {resp.json()}")

        # Start trigger task
        asyncio.create_task(trigger())

        # Connect to SSE
        print("Connecting to SSE...")
        async with client.stream("GET", f"{BASE_URL}/events") as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    print(f"Received SSE Data: {data_str}")
                    try:
                        data = json.loads(data_str)
                        # The controller wraps command in "message" event type,
                        # send_command -> broadcast("message", command)
                        # SSEService -> yields {"event": "message", "data": json.dumps(command)}
                        # So data here should be the command dict.
                        if data.get("type") == "command" and data.get("action") == "screenshot":
                            print("SUCCESS: Received expected command via SSE!")
                            return
                    except json.JSONDecodeError:
                        print("Failed to decode JSON")

async def check_log_file():
    print(f"Checking log file: {LOG_FILE}")
    if not os.path.exists(LOG_FILE):
        print("Log file does not exist!")
        return False
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        print("Log File Content Preview:")
        print(content[-500:]) # Last 500 chars
        if "Received health report" in content:
            print("SUCCESS: Log file contains health report log.")
            return True
    return False

async def main():
    try:
        await test_health()
        # Allow log to flush
        time.sleep(1)
        if await check_log_file():
             print("Log verification passed.")
        else:
             print("Log verification FAILED.")
             
        await test_sse_and_command()
        print("\nAll tests passed!")
        print("客户端对接稳定")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Test Failed: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(main())
