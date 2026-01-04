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

class CookieUpdateModel(BaseModel):
    """Cookie更新模型"""
    domain: str = Field(None, description="域名")
    xpath_config: str = Field(None, description="登录检查XPath配置")
    is_valid: bool = Field(None, description="是否有效")
    account_name: str = Field(None, description="账号名称/备注")
    test_url: str = Field(None, description="测试URL")
    status: str = Field(None, description="状态")

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

@router.put("/{id}", response_model=BaseResponse)
async def update_cookie(
    id: int,
    data: CookieUpdateModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新Cookie配置
    """
    try:
        service = CookieService(db)
        update_data = data.model_dump(exclude_unset=True)
        success = await service.update_cookie(id, update_data)
        if success:
            return BaseResponse(success=True, message="Cookie updated successfully")
        return BaseResponse(success=False, message="Cookie not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.delete("/{id}", response_model=BaseResponse)
async def delete_cookie(
    id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除Cookie
    """
    try:
        service = CookieService(db)
        success = await service.delete_cookie(id)
        if success:
            return BaseResponse(success=True, message="Cookie deleted successfully")
        return BaseResponse(success=False, message="Cookie not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))
