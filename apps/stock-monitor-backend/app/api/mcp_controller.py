"""
MCP API控制器
提供HTTP API接口，供Trae AI通过MCP工具调用
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.deepseek_mcp_service import DeepSeekMCPService, DeepSeekMessage, DeepSeekLogin, DeepSeekResponse
from app.services.collaboration_service import CollaborationService
from config.mcp_config import MCPConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP"])

# 全局服务实例
deepseek_service: Optional[DeepSeekMCPService] = None
collab_service: Optional[CollaborationService] = None


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    from app.database import get_async_session
    async for session in get_async_session():
        yield session


async def get_deepseek_service(db: AsyncSession = Depends(get_db)) -> DeepSeekMCPService:
    """获取DeepSeek服务实例"""
    global deepseek_service
    if deepseek_service is None:
        deepseek_service = DeepSeekMCPService(db)
        await deepseek_service.initialize()
    return deepseek_service


def get_collab_service() -> CollaborationService:
    """获取协作服务实例"""
    global collab_service
    if collab_service is None:
        collab_service = CollaborationService(MCPConfig.COLLABORATION_BASE_DIR)
    return collab_service


@router.get("/")
async def root():
    """根路径"""
    return {
        "message": "Trae AI MCP 协作系统运行中",
        "version": "1.0.0",
        "endpoints": {
            "deepseek": "/mcp/deepseek/*",
            "collaboration": "/mcp/collaboration/*",
            "health": "/mcp/health"
        },
        "config": {
            "deepseek_enabled": MCPConfig.MCP_TOOLS_ENABLED["deepseek"],
            "collaboration_enabled": MCPConfig.MCP_TOOLS_ENABLED["collaboration"],
            "allowed_models": MCPConfig.ALLOWED_MODELS
        }
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    import time
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "services": {
            "deepseek": deepseek_service is not None and deepseek_service.initialized,
            "collaboration": collab_service is not None
        }
    }


# ============================================================================
# DeepSeek相关API
# ============================================================================

@router.post("/deepseek/login")
async def deepseek_login(
    login_data: DeepSeekLogin,
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """DeepSeek登录"""
    try:
        result = await service.login(
            email=login_data.email,
            password=login_data.password
        )
        return result
    except Exception as e:
        logger.error(f"登录API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deepseek/send")
async def send_to_deepseek(
    message_data: DeepSeekMessage,
    from_model: Optional[str] = "GLM4.7",
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """发送消息给DeepSeek"""
    try:
        # 验证模型是否被允许
        if from_model and not MCPConfig.is_model_allowed(from_model):
            raise HTTPException(
                status_code=403,
                detail=f"模型 {from_model} 不在允许列表中"
            )
        
        result = await service.send_message(message_data, from_model=from_model)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        return result.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deepseek/session/new")
async def start_new_session(
    from_model: Optional[str] = "GLM4.7",
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """开始新的DeepSeek会话"""
    try:
        # 验证模型是否被允许
        if from_model and not MCPConfig.is_model_allowed(from_model):
            raise HTTPException(
                status_code=403,
                detail=f"模型 {from_model} 不在允许列表中"
            )
        
        result = await service.start_new_session(from_model=from_model)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始新会话API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deepseek/conversations")
async def get_conversations(
    conversation_id: Optional[str] = None,
    service: DeepSeekMCPService = Depends(get_deepseek_service)
):
    """获取对话历史"""
    try:
        result = await service.get_conversation_history(conversation_id)
        return result
    except Exception as e:
        logger.error(f"获取对话历史API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 协作文档API
# ============================================================================

@router.post("/collaboration/doc/create")
async def create_collaboration_doc(
    doc_data: dict,
    service: CollaborationService = Depends(get_collab_service),
    db: AsyncSession = Depends(get_db)
):
    """创建协作文档"""
    try:
        # 验证模型是否被允许
        author = doc_data.get("author", "GLM4.7")
        if not MCPConfig.is_model_allowed(author):
            raise HTTPException(
                status_code=403,
                detail=f"模型 {author} 不在允许列表中"
            )
        
        result = await service.create_document(
            doc_type=doc_data.get("doc_type"),
            title=doc_data.get("title"),
            content=doc_data.get("content"),
            author=author,
            db=db
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建文档API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaboration/doc/update")
async def update_collaboration_doc(
    update_data: dict,
    service: CollaborationService = Depends(get_collab_service),
    db: AsyncSession = Depends(get_db)
):
    """更新协作文档"""
    try:
        # 验证模型是否被允许
        author = update_data.get("author", "GLM4.7")
        if not MCPConfig.is_model_allowed(author):
            raise HTTPException(
                status_code=403,
                detail=f"模型 {author} 不在允许列表中"
            )
        
        result = await service.update_document(
            doc_path=update_data.get("doc_path"),
            content=update_data.get("content"),
            signature=update_data.get("signature"),
            author=author,
            db=db
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaboration/doc/{doc_path:path}")
async def get_collaboration_doc(
    doc_path: str,
    service: CollaborationService = Depends(get_collab_service)
):
    """获取协作文档"""
    try:
        result = await service.get_document(doc_path)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaboration/docs")
async def list_collaboration_docs(
    doc_type: Optional[str] = None,
    service: CollaborationService = Depends(get_collab_service)
):
    """列出协作文档"""
    try:
        result = await service.list_documents(doc_type)
        return result
    except Exception as e:
        logger.error(f"列出文档API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 协作会话API
# ============================================================================

@router.get("/collaboration/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """列出所有协作会话"""
    try:
        from app.models.collaboration_log import CollaborationSession
        from sqlalchemy import select
        
        query = select(CollaborationSession).order_by(
            CollaborationSession.updated_at.desc()
        )
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        return {
            "success": True,
            "sessions": [
                {
                    "id": session.id,
                    "session_id": session.session_id,
                    "title": session.title,
                    "doc_type": session.doc_type,
                    "status": session.status,
                    "participants": session.participants,
                    "message_count": session.message_count,
                    "version_count": session.version_count,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                }
                for session in sessions
            ],
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"列出会话API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaboration/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取特定会话"""
    try:
        from app.models.collaboration_log import CollaborationSession, CollaborationLog
        from sqlalchemy import select
        
        # 获取会话信息
        query = select(CollaborationSession).where(
            CollaborationSession.session_id == session_id
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取会话日志
        log_query = select(CollaborationLog).where(
            CollaborationLog.session_id == session_id
        ).order_by(CollaborationLog.created_at.asc())
        
        log_result = await db.execute(log_query)
        logs = log_result.scalars().all()
        
        return {
            "success": True,
            "session": {
                "id": session.id,
                "session_id": session.session_id,
                "title": session.title,
                "doc_type": session.doc_type,
                "doc_path": session.doc_path,
                "status": session.status,
                "participants": session.participants,
                "message_count": session.message_count,
                "version_count": session.version_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            },
            "logs": [
                {
                    "id": log.id,
                    "from_model": log.from_model,
                    "to_model": log.to_model,
                    "message_type": log.message_type,
                    "message_content": log.message_content,
                    "status": log.status,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话API异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))