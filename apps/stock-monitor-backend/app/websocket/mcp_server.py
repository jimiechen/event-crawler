"""
MCP WebSocket Server
Handles WebSocket connections from Chrome Extension
"""

import asyncio
import json
import struct
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, Callable
import websockets
from websockets.server import WebSocketServerProtocol


class MCPServer:
    """MCP WebSocket Server"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.running = False
        
    async def start(self):
        """Start the WebSocket server"""
        self.running = True
        print(f"Starting MCP WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        ):
            await asyncio.Future()  # Run forever
            
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client connection"""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        
        print(f"Client connected: {client_id}")
        
        try:
            # Send connection acknowledgment
            await self.send_message(websocket, {
                "type": "connect_ack",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                try:
                    await self.handle_message(client_id, websocket, message)
                except Exception as e:
                    print(f"Error handling message from {client_id}: {e}")
                    await self.send_message(websocket, {
                        "type": "error",
                        "error": str(e)
                    })
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Client disconnected: {client_id}")
        finally:
            del self.clients[client_id]
            
    async def handle_message(self, client_id: str, websocket: WebSocketServerProtocol, message: bytes):
        """Handle incoming message"""
        # Parse binary message
        msg_type, payload = self.decode_message(message)
        
        print(f"Received message type {msg_type} from {client_id}")
        
        if msg_type == 10:  # SKILL_REQUEST
            await self.handle_skill_request(client_id, websocket, payload)
        elif msg_type == 3:  # HEARTBEAT
            await self.send_message(websocket, {
                "type": "heartbeat_ack",
                "timestamp": datetime.now().isoformat()
            })
        elif msg_type == 1:  # CONNECT
            print(f"Client {client_id} sent connect message")
        else:
            print(f"Unknown message type: {msg_type}")
            
    async def handle_skill_request(self, client_id: str, websocket: WebSocketServerProtocol, payload: bytes):
        """Handle skill request"""
        try:
            request = json.loads(payload.decode('utf-8'))
            skill_name = request.get('skill_name')
            parameters = request.get('parameters', {})
            request_id = request.get('request_id')
            
            print(f"Executing skill: {skill_name} with params: {parameters}")
            
            # Execute skill (placeholder - would call actual skill executor)
            result = await self.execute_skill(skill_name, parameters)
            
            # Send response
            response = {
                "type": "skill_response",
                "request_id": request_id,
                "success": True,
                "result": json.dumps(result),
                "processing_time_ms": 100
            }
            
            await self.send_message(websocket, response)
            
        except Exception as e:
            print(f"Error executing skill: {e}")
            await self.send_message(websocket, {
                "type": "skill_response",
                "request_id": request.get('request_id'),
                "success": False,
                "error": str(e)
            })
            
    async def execute_skill(self, skill_name: str, parameters: dict) -> dict:
        """Execute a skill"""
        # Placeholder implementation
        # In real implementation, this would call the skill registry
        return {
            "skill": skill_name,
            "parameters": parameters,
            "executed_at": datetime.now().isoformat(),
            "status": "success"
        }
        
    async def send_message(self, websocket: WebSocketServerProtocol, message: dict):
        """Send message to client"""
        encoded = self.encode_message(message)
        await websocket.send(encoded)
        
    def encode_message(self, message: dict) -> bytes:
        """Encode message to binary format"""
        payload = json.dumps(message).encode('utf-8')
        
        # Simple binary format: [type(1)][payload_len(4)][payload]
        msg_type = message.get('type', 'unknown')
        type_map = {
            'connect_ack': 2,
            'skill_response': 11,
            'skill_stream': 12,
            'heartbeat_ack': 4,
            'error': 99
        }
        type_code = type_map.get(msg_type, 0)
        
        buffer = struct.pack('<BI', type_code, len(payload)) + payload
        return buffer
        
    def decode_message(self, data: bytes) -> tuple:
        """Decode binary message"""
        if len(data) < 5:
            return 0, b''
            
        type_code = struct.unpack('<B', data[0:1])[0]
        payload_len = struct.unpack('<I', data[1:5])[0]
        payload = data[5:5+payload_len]
        
        return type_code, payload
        
    async def broadcast(self, message: dict):
        """Broadcast message to all clients"""
        encoded = self.encode_message(message)
        for client in self.clients.values():
            try:
                await client.send(encoded)
            except:
                pass


# Run server
if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.start())
