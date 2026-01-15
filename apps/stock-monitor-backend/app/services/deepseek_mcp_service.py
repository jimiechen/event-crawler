"""
DeepSeek MCP服务
封装DeepSeek爬虫能力为MCP工具
"""
import asyncio
import json
import os
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from app.crawler.deepseek_crawler import DeepSeekCrawler
from app.models.collaboration_log import CollaborationLog
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class DeepSeekMessage(BaseModel):
    """DeepSeek消息模型"""
    message: str
    conversation_id: Optional[str] = None


class DeepSeekLogin(BaseModel):
    """DeepSeek登录模型"""
    email: str
    password: str


class DeepSeekResponse(BaseModel):
    """DeepSeek响应模型"""
    success: bool
    response: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class DeepSeekMCPService:
    """DeepSeek MCP服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crawler: Optional[DeepSeekCrawler] = None
        self.initialized = False
        self.active_conversations = {}  # conversation_id -> metadata
        
    async def initialize(self):
        """初始化服务"""
        if not self.initialized:
            self.crawler = DeepSeekCrawler(self.db, "deepseek")
            success = await self.crawler.initialize()
            if success:
                self.initialized = True
                logger.info("DeepSeek MCP服务初始化完成")
            else:
                logger.error("DeepSeek MCP服务初始化失败")
            return success
        return True
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """登录DeepSeek"""
        try:
            if not self.crawler:
                await self.initialize()
                
            success = await self.crawler.login(email, password)
            
            # 记录协作日志
            log = CollaborationLog(
                conversation_id="login",
                session_id="system",
                from_model="system",
                to_model="DeepSeek",
                message_type="login_request",
                message_content=f"登录请求: {email}",
                status="completed" if success else "failed"
            )
            self.db.add(log)
            await self.db.commit()
            
            return {
                "success": success,
                "message": "登录成功" if success else "登录失败"
            }
        except Exception as e:
            logger.error(f"登录服务异常: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_message(self, message_data: DeepSeekMessage, from_model: str = "GLM4.7") -> DeepSeekResponse:
        """发送消息给DeepSeek"""
        try:
            if not self.crawler or not self.crawler.is_logged_in:
                # 尝试从环境变量获取登录信息
                email = os.getenv("DEEPSEEK_EMAIL")
                password = os.getenv("DEEPSEEK_PASSWORD")
                
                if email and password:
                    await self.login(email, password)
                else:
                    return DeepSeekResponse(
                        success=False,
                        error="未登录且无环境变量配置"
                    )
            
            # 记录请求日志
            request_log = CollaborationLog(
                conversation_id=message_data.conversation_id,
                session_id="mcp",
                from_model=from_model,
                to_model="DeepSeek",
                message_type="request",
                message_content=message_data.message,
                status="processing"
            )
            self.db.add(request_log)
            await self.db.commit()
            
            # 发送消息
            result = await self.crawler.send_message(
                message=message_data.message,
                conversation_id=message_data.conversation_id
            )
            
            # 记录响应日志
            response_log = CollaborationLog(
                conversation_id=message_data.conversation_id,
                session_id="mcp",
                from_model="DeepSeek",
                to_model=from_model,
                message_type="response",
                message_content=result.get("response", ""),
                status="completed" if result.get("success") else "failed",
                error_message=result.get("error")
            )
            self.db.add(response_log)
            await self.db.commit()
            
            # 记录对话
            if result["success"] and result["conversation_id"]:
                self.active_conversations[result["conversation_id"]] = {
                    "last_message": message_data.message,
                    "last_response": result["response"],
                    "timestamp": result["timestamp"],
                    "from_model": from_model
                }
            
            return DeepSeekResponse(**result)
            
        except Exception as e:
            logger.error(f"发送消息服务异常: {str(e)}")
            
            # 记录错误日志
            error_log = CollaborationLog(
                conversation_id=message_data.conversation_id,
                session_id="mcp",
                from_model=from_model,
                to_model="DeepSeek",
                message_type="error",
                message_content=message_data.message,
                status="failed",
                error_message=str(e)
            )
            self.db.add(error_log)
            await self.db.commit()
            
            return DeepSeekResponse(
                success=False,
                error=str(e)
            )
    
    async def start_new_session(self, from_model: str = "GLM4.7") -> Dict[str, Any]:
        """开始新的会话"""
        try:
            if not self.crawler or not self.crawler.is_logged_in:
                return {
                    "success": False,
                    "error": "请先登录DeepSeek"
                }
            
            success = await self.crawler.start_new_conversation()
            conversation_id = str(int(time.time()))
            
            self.active_conversations[conversation_id] = {
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "message_count": 0,
                "from_model": from_model
            }
            
            # 记录会话日志
            log = CollaborationLog(
                conversation_id=conversation_id,
                session_id="mcp",
                from_model=from_model,
                to_model="DeepSeek",
                message_type="session_start",
                message_content="开始新会话",
                status="completed" if success else "failed"
            )
            self.db.add(log)
            await self.db.commit()
            
            return {
                "success": success,
                "conversation_id": conversation_id,
                "message": "新会话已开始" if success else "开始新会话失败"
            }
            
        except Exception as e:
            logger.error(f"开始新会话异常: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_conversation_history(self, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """获取对话历史"""
        try:
            if conversation_id:
                # 获取特定对话
                if conversation_id in self.active_conversations:
                    return {
                        "success": True,
                        "conversation": self.active_conversations[conversation_id]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"对话 {conversation_id} 不存在"
                    }
            else:
                # 获取所有活跃对话
                return {
                    "success": True,
                    "conversations": self.active_conversations
                }
                
        except Exception as e:
            logger.error(f"获取对话历史异常: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.crawler:
                await self.crawler.close()
            self.initialized = False
            logger.info("DeepSeek MCP服务已清理")
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")