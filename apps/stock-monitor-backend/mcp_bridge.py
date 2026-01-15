#!/usr/bin/env python3
"""
DeepSeek MCP Bridge for Trae
Connects Trae MCP client to the running Stock Monitor Backend Service
"""

import sys
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

# MCP Server Configuration
mcp = FastMCP("DeepSeek Bridge")

# Backend Configuration
BACKEND_URL = "http://127.0.0.1:56666/mcp/deepseek"

@mcp.tool()
async def list_chats() -> str:
    """List historical chats from DeepSeek"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/chats", timeout=30.0)
            response.raise_for_status()
            return str(response.json())
        except Exception as e:
            return f"Error fetching chats: {str(e)}"

@mcp.tool()
async def read_chat(chat_id: str) -> str:
    """Read content of a specific chat session"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/chats/{chat_id}", timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data.get("content", "")
        except Exception as e:
            return f"Error reading chat: {str(e)}"

@mcp.tool()
async def send_message(text: str, chat_id: str = None) -> str:
    """Send a message to DeepSeek and get response"""
    async with httpx.AsyncClient() as client:
        try:
            payload = {"text": text}
            if chat_id:
                payload["chat_id"] = chat_id
                
            response = await client.post(
                f"{BACKEND_URL}/send", 
                json=payload,
                timeout=120.0 # Long timeout for AI generation
            )
            response.raise_for_status()
            data = response.json()
            return data.get("reply", "")
        except Exception as e:
            return f"Error sending message: {str(e)}"

if __name__ == "__main__":
    mcp.run()
