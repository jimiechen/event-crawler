"""
DeepSeek MCP服务
封装DeepSeek爬虫能力为MCP工具
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.crawler.deepseek_crawler import DeepSeekCrawler

logger = logging.getLogger(__name__)

class DeepSeekMCPService:
    """DeepSeek MCP服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crawler = DeepSeekCrawler(db, "deepseek")
        
    async def list_chats(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return await self.crawler.list_chats()
        
    async def read_chat(self, chat_id: str = "latest") -> str:
        """读取会话内容"""
        return await self.crawler.read_chat(chat_id)
        
    async def send_message(self, text: str, chat_id: Optional[str] = None) -> str:
        """发送消息"""
        return await self.crawler.send_message(text, chat_id)
