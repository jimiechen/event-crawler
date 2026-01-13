#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台管理API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db_session
from app.services.platform_service import PlatformService
from app.api.schemas import BaseResponse

router = APIRouter(prefix="/api/v1/platforms", tags=["Platforms"])


class PlatformCreateModel(BaseModel):
    """创建平台请求"""
    platform_id: str = Field(..., description="平台标识")
    name: str = Field(..., description="平台名称")
    domain: str = Field(..., description="Cookie域名")
    login_url: str = Field(None, description="登录URL")
    home_url: str = Field(None, description="首页URL")
    verify_api: str = Field(None, description="验证API")
    verify_type: str = Field(default="json", description="验证类型")
    verify_xpath: str = Field(None, description="XPath配置")
    verify_parser: str = Field(None, description="解析器配置")
    icon: str = Field(None, description="平台图标")


class PlatformUpdateModel(BaseModel):
    """更新平台请求"""
    name: str = Field(None, description="平台名称")
    domain: str = Field(None, description="Cookie域名")
    login_url: str = Field(None, description="登录URL")
    home_url: str = Field(None, description="首页URL")
    verify_api: str = Field(None, description="验证API")
    verify_type: str = Field(None, description="验证类型")
    verify_xpath: str = Field(None, description="XPath配置")
    verify_parser: str = Field(None, description="解析器配置")
    icon: str = Field(None, description="平台图标")


@router.get("", response_model=BaseResponse)
async def get_all_platforms(
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取所有平台列表
    """
    try:
        service = PlatformService(db)
        data = await service.get_all_platforms()
        return BaseResponse(
            success=True,
            message="Success",
            data=data
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.get("/{platform_id}", response_model=BaseResponse)
async def get_platform(
    platform_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取指定平台配置
    """
    try:
        service = PlatformService(db)
        data = await service.get_platform_by_id(platform_id)
        if data:
            return BaseResponse(
                success=True,
                message="Success",
                data=data
            )
        return BaseResponse(success=False, message="Platform not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.post("", response_model=BaseResponse)
async def create_platform(
    data: PlatformCreateModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    创建平台配置
    """
    try:
        service = PlatformService(db)
        result = await service.create_platform(data.model_dump())
        return BaseResponse(
            success=True,
            message="Platform created successfully",
            data=result
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.put("/{platform_id}", response_model=BaseResponse)
async def update_platform(
    platform_id: str,
    data: PlatformUpdateModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新平台配置
    """
    try:
        service = PlatformService(db)
        update_data = data.model_dump(exclude_unset=True)
        success = await service.update_platform(platform_id, update_data)
        if success:
            return BaseResponse(success=True, message="Platform updated successfully")
        return BaseResponse(success=False, message="Platform not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.delete("/{platform_id}", response_model=BaseResponse)
async def delete_platform(
    platform_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除平台配置
    """
    try:
        service = PlatformService(db)
        success = await service.delete_platform(platform_id)
        if success:
            return BaseResponse(success=True, message="Platform deleted successfully")
        return BaseResponse(success=False, message="Platform not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))
