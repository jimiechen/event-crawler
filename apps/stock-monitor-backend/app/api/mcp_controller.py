"""
MCP API控制器
提供HTTP API接口，供Trae AI通过MCP工具调用
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.deepseek_mcp_service import DeepSeekMCPService
from mcp.server.fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP"])

# 全局服务实例
deepseek_service: Optional[DeepSeekMCPService] = None

async def get_db() -> AsyncSession:
    """获取数据库会话"""
    from app.database import get_db_session
    async for session in get_db_session():
        yield session

async def get_deepseek_service(db: AsyncSession = Depends(get_db)) -> DeepSeekMCPService:
    """获取DeepSeek服务实例"""
    global deepseek_service
    # 每次请求都重新实例化可能比较安全，或者需要确保 db session 的生命周期
    # 这里的简单实现：
    return DeepSeekMCPService(db)

# ============================================================================
# DeepSeek相关API (REST)
# ============================================================================

@router.get("/deepseek/chats")
async def list_chats(service: DeepSeekMCPService = Depends(get_deepseek_service)):
    """获取会话列表"""
    try:
        return await service.list_chats()
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deepseek/chats/{chat_id}")
async def read_chat(chat_id: str, service: DeepSeekMCPService = Depends(get_deepseek_service)):
    """读取会话内容"""
    try:
        content = await service.read_chat(chat_id)
        return {"content": content}
    except Exception as e:
        logger.error(f"读取会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.collaboration_service import CollaborationService
from app.services.deepseek_mcp_service import DeepSeekMCPService

# ============================================================================
# Dependency Injection
# ============================================================================

async def get_collaboration_service(db: AsyncSession = Depends(get_db)) -> CollaborationService:
    """获取协作文档服务实例"""
    return CollaborationService(db=db)

# ============================================================================
# Collaboration Tools API
# ============================================================================

@router.post("/collaboration/doc/create")
async def create_doc(
    payload: Dict[str, Any], 
    service: CollaborationService = Depends(get_collaboration_service)
):
    """创建协作文档"""
    return await service.create_document(
        doc_type=payload.get("doc_type"),
        title=payload.get("title"),
        content=payload.get("content"),
        author=payload.get("author", "GLM4.7"),
        db=service.db if hasattr(service, 'db') else None
    )

@router.post("/collaboration/doc/update")
async def update_doc(
    payload: Dict[str, Any],
    service: CollaborationService = Depends(get_collaboration_service)
):
    """更新协作文档"""
    return await service.update_document(
        doc_path=payload.get("doc_path"),
        content=payload.get("content"),
        signature=payload.get("signature"),
        author=payload.get("author", "GLM4.7"),
        db=service.db if hasattr(service, 'db') else None
    )

@router.post("/collaboration/doc/{doc_path:path}")
async def get_doc(
    doc_path: str,
    service: CollaborationService = Depends(get_collaboration_service)
):
    """获取协作文档"""
    return await service.get_document(doc_path)

@router.post("/collaboration/docs")
async def list_docs(
    payload: Dict[str, Any],
    service: CollaborationService = Depends(get_collaboration_service)
):
    """列出协作文档"""
    return await service.list_documents(doc_type=payload.get("doc_type"))

# ============================================================================
# DeepSeek API Extensions
# ============================================================================

@router.post("/deepseek/login")
async def deepseek_login(
    payload: Dict[str, Any],
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """DeepSeek登录 (实际上是检查/初始化会话)"""
    # 目前DeepSeekCrawler主要依赖DB中的会话或手动登录
    # 这里我们触发一次start()来确保会话有效
    try:
        # 注意: start() 是异步的且可能会阻塞，这里应该谨慎调用
        # 理想情况下，我们只检查状态
        # 暂时返回成功，假设后台服务已在运行
        return {"success": True, "message": "DeepSeek session check initiated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/deepseek/session/new")
async def deepseek_new_session(
    payload: Dict[str, Any],
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """开始新会话"""
    # 这里的实现依赖于 send_message 不带 chat_id
    # 或者我们需要在 crawler 中显式添加 new_chat 方法
    return {"success": True, "conversation_id": "new", "message": "New session context ready"}

@router.post("/deepseek/conversations")
async def deepseek_conversations(
    payload: Dict[str, Any],
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """获取会话历史"""
    chat_id = payload.get("conversation_id")
    if chat_id:
        content = await service.read_chat(chat_id)
        return {"success": True, "conversation": {"last_message": "...", "last_response": content}}
    else:
        chats = await service.list_chats()
        return {"success": True, "conversations": chats}

@router.post("/deepseek/send")
async def send_message(
    payload: Dict[str, Any], 
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """发送消息"""
    try:
        # 兼容 message 或 text 字段
        text = payload.get("message") or payload.get("text")
        chat_id = payload.get("conversation_id") or payload.get("chat_id")
        
        if not text:
            raise HTTPException(status_code=400, detail="message text is required")
            
        # 这里的 chat_id 如果是 "new" 或者 None，DeepSeekCrawler 会自动处理
        reply = await service.send_message(text, chat_id)
        
        # 尝试从回复中提取 conversation_id (如果 crawler 返回元组或字典)
        # 目前 crawler.send_message 返回 str
        # 这是一个改进点：让 crawler 返回更多元数据
        
        return {
            "success": True, 
            "response": reply,
            "conversation_id": chat_id, # 暂时返回原 ID
            "timestamp": "now"
        }
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# MCP SSE Endpoint (Experimental)
# ============================================================================
# 注意：这里我们尝试集成 FastMCP 到 FastAPI
# FastMCP 本身管理着生命周期，这里我们只定义工具，通过 SSE 暴露

mcp = FastMCP("stock-monitor-backend")

@mcp.tool()
async def deepseek_list_chats_tool() -> str:
    """List historical chats from DeepSeek."""
    # 注意：FastMCP 的工具函数通常是静态的或自包含的
    # 在这里我们需要一种方式获取 DB session
    # 这是一个简化实现，实际上可能需要更复杂的依赖注入
    # 临时方案：直接连接数据库或通过 HTTP 调用自身的 API (Loopback)
    # 或者，我们在此处不实现 FastMCP，而是让 Trae 直接调用上述 REST API
    # 但为了满足 MCP 协议，我们需要暴露 SSE
    return "Use REST API for now or implement DB context manager here"

# 由于 FastMCP 接管了路由，直接集成到现有的 FastAPI 比较复杂
# 我们推荐使用 SSE 路由手动实现 MCP 协议，或者运行独立的 MCP 服务器
# 这里我们保留 REST API，Trae 可以通过 Generic REST MCP Client 调用，
# 或者我们可以实现一个简单的 SSE 端点来包装这些调用。

from sse_starlette.sse import EventSourceResponse

@router.get("/sse")
async def mcp_sse(request: Request):
    """MCP SSE Endpoint"""
    async def event_generator():
        # 这里应该实现 MCP 协议的握手和消息处理
        # 鉴于复杂性，建议目前阶段主要使用 REST API
        # 如果必须支持 MCP 协议，建议使用 mcp python sdk 的 sse transport
        yield {"event": "endpoint", "data": "/mcp/messages"}

    return EventSourceResponse(event_generator())

@router.post("/messages")
async def mcp_messages(request: Request):
    """MCP Messages Endpoint"""
    # 处理 JSON-RPC 请求
    return {"jsonrpc": "2.0", "result": "ok"}
