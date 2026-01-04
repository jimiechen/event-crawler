import asyncio
from typing import List, Dict, Any
from fastapi import Request
from sse_starlette.sse import EventSourceResponse
from loguru import logger
import json

class SSEService:
    def __init__(self):
        self.clients: List[asyncio.Queue] = []

    async def subscribe(self, request: Request):
        queue = asyncio.Queue()
        self.clients.append(queue)
        logger.info(f"New SSE client connected. Total clients: {len(self.clients)}")

        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    
                    # Get message from queue
                    data = await queue.get()
                    yield data
            except asyncio.CancelledError:
                logger.info("SSE client disconnected")
            finally:
                self.clients.remove(queue)
                logger.info(f"SSE client removed. Total clients: {len(self.clients)}")

        return EventSourceResponse(event_generator())

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast message to all connected clients
        """
        message = {
            "event": event_type,
            "data": json.dumps(data)
        }
        
        # Remove dead clients (optional, handled in generator usually)
        # But here we just put to queue
        for queue in self.clients:
            await queue.put(message)
            
        logger.debug(f"Broadcasted event {event_type} to {len(self.clients)} clients")

# Global instance
sse_service = SSEService()
