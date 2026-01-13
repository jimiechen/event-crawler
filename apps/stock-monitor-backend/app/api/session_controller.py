#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.database import get_db_session
from app.services.session_service import SessionService
from app.api.schemas import BaseResponse

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


class SessionCreateModel(BaseModel):
    """创建/更新会话请求"""
    platform_id: str = Field(..., description="平台标识")
    user_id: str = Field(..., description="用户ID/账号标识")
    account_name: str = Field(..., description="账号名称/昵称")
    cookies: List[Dict[str, Any]] = Field(..., description="Cookie列表")
    user_agent: str = Field(None, description="User-Agent")


class SessionVerifyModel(BaseModel):
    """验证会话请求"""
    success: bool = Field(..., description="是否验证成功")


@router.post("", response_model=BaseResponse)
async def upsert_session(
    data: SessionCreateModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    创建或更新会话
    """
    try:
        service = SessionService(db)
        result = await service.upsert_session(
            platform_id=data.platform_id,
            user_id=data.user_id,
            account_name=data.account_name,
            cookies=data.cookies,
            user_agent=data.user_agent
        )
        return BaseResponse(
            success=True,
            message=f"Session updated for user: {data.account_name}",
            data=result
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.get("/{platform_id}", response_model=BaseResponse)
async def get_sessions_by_platform(
    platform_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取指定平台的所有会话
    """
    try:
        service = SessionService(db)
        data = await service.get_sessions_by_platform(platform_id)
        return BaseResponse(
            success=True,
            message="Success",
            data=data
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.get("/{platform_id}/best", response_model=BaseResponse)
async def get_best_session(
    platform_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取最佳会话（爬虫调用）
    """
    try:
        service = SessionService(db)
        data = await service.get_best_session(platform_id)
        if data:
            return BaseResponse(
                success=True,
                message="Best session found",
                data=data
            )
        return BaseResponse(
            success=False,
            message="No active session found for this platform"
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.post("/{session_id}/verify", response_model=BaseResponse)
async def verify_session(
    session_id: int,
    data: SessionVerifyModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    验证会话并更新健康度
    """
    try:
        service = SessionService(db)
        success = await service.verify_session(session_id, data.success)
        if success:
            return BaseResponse(
                success=True,
                message="Session verified successfully"
            )
        return BaseResponse(success=False, message="Session not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.delete("/{session_id}", response_model=BaseResponse)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除会话
    """
    try:
        service = SessionService(db)
        success = await service.delete_session(session_id)
        if success:
            return BaseResponse(success=True, message="Session deleted successfully")
        return BaseResponse(success=False, message="Session not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))
