#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie管理API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.database import get_db_session
from app.services.cookie_service import CookieService
from app.api.schemas import BaseResponse

router = APIRouter(prefix="/api/v1/cookies", tags=["Cookies"])

class CookieDataModel(BaseModel):
    """Cookie数据模型"""
    domain: str = Field(..., description="域名")
    cookies: List[Dict[str, Any]] = Field(..., description="Cookie列表")

@router.post("", response_model=BaseResponse)
async def sync_cookies(
    data: CookieDataModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    同步Cookie数据
    """
    try:
        service = CookieService(db)
        await service.sync_cookies(data.domain, data.cookies)
        return BaseResponse(
            success=True,
            message=f"Successfully synced cookies for {data.domain}",
            data={"count": len(data.cookies)}
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.get("", response_model=BaseResponse)
async def get_all_cookies_list(
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取所有Cookie域名列表
    """
    try:
        service = CookieService(db)
        data = await service.get_all_cookies()
        return BaseResponse(
            success=True,
            message="Success",
            data=data
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.get("/{domain}", response_model=BaseResponse)
async def get_cookies(
    domain: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取指定域名的Cookie
    """
    try:
        service = CookieService(db)
        cookies = await service.get_cookies(domain)
        if cookies:
            return BaseResponse(
                success=True,
                message="Cookies found",
                data=cookies
            )
        else:
            return BaseResponse(
                success=False,
                message="No cookies found for this domain"
            )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))
