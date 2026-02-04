"""
Session Management API
Handles user session storage and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db_session
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionData(BaseModel):
    """Session data model"""
    platform: str
    cookies: Optional[Dict[str, Any]] = None
    tokens: Optional[Dict[str, str]] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Session response model"""
    id: str
    platform: str
    created_at: datetime
    updated_at: datetime
    is_active: bool


@router.post("/")
async def save_session(
    data: SessionData,
    db: AsyncSession = Depends(get_db_session)
):
    """Save or update platform session data"""
    try:
        service = SessionService(db)
        session = await service.save_session(
            platform=data.platform,
            cookies=data.cookies,
            tokens=data.tokens,
            user_agent=data.user_agent,
            metadata=data.metadata
        )
        return {
            "success": True,
            "session": {
                "id": session.id,
                "platform": session.platform,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}")
async def get_session(
    platform: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get session data for a platform"""
    try:
        service = SessionService(db)
        session = await service.get_session(platform)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found for platform: {platform}")
        
        return {
            "success": True,
            "session": {
                "id": session.id,
                "platform": session.platform,
                "cookies": session.cookies,
                "tokens": session.tokens,
                "user_agent": session.user_agent,
                "metadata": session.metadata,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{platform}/refresh")
async def refresh_session(
    platform: str,
    data: SessionData,
    db: AsyncSession = Depends(get_db_session)
):
    """Refresh session data (update cookies/tokens)"""
    try:
        service = SessionService(db)
        session = await service.update_session(
            platform=platform,
            cookies=data.cookies,
            tokens=data.tokens,
            user_agent=data.user_agent,
            metadata=data.metadata
        )
        return {
            "success": True,
            "session": {
                "id": session.id,
                "platform": session.platform,
                "updated_at": session.updated_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{platform}")
async def delete_session(
    platform: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete session for a platform"""
    try:
        service = SessionService(db)
        await service.delete_session(platform)
        return {"success": True, "message": f"Session for {platform} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_sessions(
    db: AsyncSession = Depends(get_db_session)
):
    """List all active sessions"""
    try:
        service = SessionService(db)
        sessions = await service.list_sessions()
        return {
            "success": True,
            "sessions": [
                {
                    "id": s.id,
                    "platform": s.platform,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                    "is_active": s.is_active
                }
                for s in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
