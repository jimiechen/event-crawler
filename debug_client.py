import asyncio
import json
import websockets
import sys
import os

# 颜色配置
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def log(level, message):
    if level == 'info':
        print(f"{GREEN}[INFO] {message}{RESET}")
    elif level == 'error':
        print(f"{RED}[ERROR] {message}{RESET}")
    elif level == 'warn':
        print(f"{YELLOW}[WARN] {message}{RESET}")

async def test_native_server_connection():
    uri = "ws://localhost:3000/api/ws"
    log('info', f"Connecting to Native Server at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            log('info', "Connected to Native Server via WebSocket")
            
            # 监听消息
            log('info', "Waiting for messages from Chrome Extension...")
            
            # 发送测试消息
            test_msg = {
                "type": "CLIENT_TEST",
                "payload": {
                    "message": "Hello from Python Debug Client",
                    "timestamp": "now"
                }
            }
            await websocket.send(json.dumps(test_msg))
            log('info', f"Sent test message: {test_msg}")
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60)
                    data = json.loads(message)
                    log('info', f"Received message: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    if data.get('type') == 'FORWARD_TO_NATIVE':
                        log('info', ">>> 收到来自Chrome扩展的转发数据!")
                        
                except asyncio.TimeoutError:
                    log('warn', "No message received in 60 seconds, sending heartbeat...")
                    await websocket.send(json.dumps({"type": "ping"}))
                    
    except ConnectionRefusedError:
        log('error', "Connection refused. Is Native Server running on port 3000?")
    except Exception as e:
        log('error', f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_native_server_connection())
    except KeyboardInterrupt:
        log('info', "Debug client stopped by user")
