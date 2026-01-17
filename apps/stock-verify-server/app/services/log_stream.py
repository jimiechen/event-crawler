import asyncio
from typing import List
from datetime import datetime

class LogStreamManager:
    def __init__(self):
        self.queues: List[asyncio.Queue] = []

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.queues.append(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.queues:
            self.queues.remove(queue)

    async def broadcast(self, message: str, step: str = None, status: str = None):
        """
        Broadcast a message to all connected clients.
        format: JSON string with timestamp, message, step, status
        """
        payload = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": message,
            "step": step,
            "status": status
        }
        for queue in self.queues:
            await queue.put(payload)

# Global instance
log_manager = LogStreamManager()
