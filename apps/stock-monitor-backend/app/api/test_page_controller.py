#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试页面API控制器
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database import get_db_session
from app.models.test_page import TestPage, TestResult
from app.api.schemas import BaseResponse

router = APIRouter(prefix="/api/v1/test-pages", tags=["Test Pages"])


class TestPageCreateModel(BaseModel):
    """创建测试页面请求"""
    name: str = Field(..., description="测试页面名称")
    url: str = Field(..., description="测试页面URL")
    platform: str = Field(..., description="平台标识")
    description: Optional[str] = Field(None, description="页面描述")


class TestPageUpdateModel(BaseModel):
    """更新测试页面请求"""
    name: Optional[str] = Field(None, description="测试页面名称")
    url: Optional[str] = Field(None, description="测试页面URL")
    description: Optional[str] = Field(None, description="页面描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class TestRunModel(BaseModel):
    """运行测试请求"""
    test_page_id: int = Field(..., description="测试页面ID")
    test_type: str = Field(..., description="测试类型：session/crawler")


@router.get("", response_model=BaseResponse)
async def get_test_pages(db: AsyncSession = Depends(get_db_session)):
    """
    获取所有测试页面
    """
    try:
        from sqlalchemy import select
        stmt = select(TestPage).order_by(TestPage.created_at.desc())
        result = await db.execute(stmt)
        test_pages = result.scalars().all()
        
        return BaseResponse(
            success=True,
            message="Success",
            data=[
                {
                    "id": tp.id,
                    "name": tp.name,
                    "url": tp.url,
                    "platform": tp.platform,
                    "description": tp.description,
                    "is_active": tp.is_active,
                    "created_at": tp.created_at.isoformat() if tp.created_at else None,
                    "updated_at": tp.updated_at.isoformat() if tp.updated_at else None,
                    "test_results": tp.test_results
                }
                for tp in test_pages
            ]
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.post("", response_model=BaseResponse)
async def create_test_page(data: TestPageCreateModel, db: AsyncSession = Depends(get_db_session)):
    """
    创建测试页面
    """
    try:
        test_page = TestPage(
            name=data.name,
            url=data.url,
            platform=data.platform,
            description=data.description
        )
        db.add(test_page)
        await db.commit()
        await db.refresh(test_page)
        
        return BaseResponse(
            success=True,
            message="Test page created successfully",
            data={
                "id": test_page.id,
                "name": test_page.name
            }
        )
    except Exception as e:
        await db.rollback()
        return BaseResponse(success=False, message=str(e))


@router.put("/{page_id}", response_model=BaseResponse)
async def update_test_page(
    page_id: int,
    data: TestPageUpdateModel,
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新测试页面
    """
    try:
        from sqlalchemy import select
        stmt = select(TestPage).where(TestPage.id == page_id)
        result = await db.execute(stmt)
        test_page = result.scalar_one_or_none()
        
        if not test_page:
            raise HTTPException(status_code=404, detail="Test page not found")
        
        if data.name is not None:
            test_page.name = data.name
        if data.url is not None:
            test_page.url = data.url
        if data.description is not None:
            test_page.description = data.description
        if data.is_active is not None:
            test_page.is_active = data.is_active
        
        test_page.updated_at = datetime.now()
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="Test page updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return BaseResponse(success=False, message=str(e))


@router.delete("/{page_id}", response_model=BaseResponse)
async def delete_test_page(page_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    删除测试页面
    """
    try:
        from sqlalchemy import select
        stmt = select(TestPage).where(TestPage.id == page_id)
        result = await db.execute(stmt)
        test_page = result.scalar_one_or_none()
        
        if not test_page:
            raise HTTPException(status_code=404, detail="Test page not found")
        
        await db.delete(test_page)
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="Test page deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return BaseResponse(success=False, message=str(e))


@router.post("/run", response_model=BaseResponse)
async def run_test(data: TestRunModel, db: AsyncSession = Depends(get_db_session)):
    """
    运行测试
    """
    import time
    start_time = time.time()
    
    try:
        from sqlalchemy import select
        stmt = select(TestPage).where(TestPage.id == data.test_page_id)
        result = await db.execute(stmt)
        test_page = result.scalar_one_or_none()
        
        if not test_page:
            raise HTTPException(status_code=404, detail="Test page not found")
        
        if not test_page.is_active:
            raise HTTPException(status_code=400, detail="Test page is not active")
        
        # 根据测试类型执行不同的测试
        if data.test_type == "session":
            test_result = await run_session_test(test_page, db)
        elif data.test_type == "crawler":
            test_result = await run_crawler_test(test_page, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid test type")
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 保存测试结果
        test_result_record = TestResult(
            test_page_id=test_page.id,
            test_type=data.test_type,
            status=test_result["status"],
            message=test_result["message"],
            result_data=test_result.get("data"),
            tested_at=datetime.now(),
            duration_ms=duration_ms
        )
        db.add(test_result_record)
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="Test completed",
            data=test_result
        )
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 保存失败结果
        try:
            test_result_record = TestResult(
                test_page_id=data.test_page_id,
                test_type=data.test_type,
                status="failed",
                message=str(e),
                result_data=None,
                tested_at=datetime.now(),
                duration_ms=duration_ms
            )
            db.add(test_result_record)
            await db.commit()
        except:
            pass
        
        return BaseResponse(success=False, message=str(e))


@router.get("/results", response_model=BaseResponse)
async def get_all_test_results(db: AsyncSession = Depends(get_db_session)):
    """
    获取所有测试结果
    """
    try:
        from sqlalchemy import select
        stmt = select(TestResult).order_by(TestResult.tested_at.desc())
        result = await db.execute(stmt)
        test_results = result.scalars().all()
        
        return BaseResponse(
            success=True,
            message="Success",
            data=[
                {
                    "id": tr.id,
                    "test_page_id": tr.test_page_id,
                    "test_type": tr.test_type,
                    "status": tr.status,
                    "message": tr.message,
                    "result_data": tr.result_data,
                    "tested_at": tr.tested_at.isoformat() if tr.tested_at else None,
                    "duration_ms": tr.duration_ms
                }
                for tr in test_results
            ]
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.get("/{page_id}/results", response_model=BaseResponse)
async def get_test_results(page_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    获取测试结果
    """
    try:
        from sqlalchemy import select
        stmt = select(TestResult).where(TestResult.test_page_id == page_id).order_by(TestResult.tested_at.desc())
        result = await db.execute(stmt)
        test_results = result.scalars().all()
        
        return BaseResponse(
            success=True,
            message="Success",
            data=[
                {
                    "id": tr.id,
                    "test_type": tr.test_type,
                    "status": tr.status,
                    "message": tr.message,
                    "result_data": tr.result_data,
                    "tested_at": tr.tested_at.isoformat() if tr.tested_at else None,
                    "duration_ms": tr.duration_ms
                }
                for tr in test_results
            ]
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


async def run_session_test(test_page: TestPage, db: AsyncSession) -> Dict[str, Any]:
    """
    运行会话测试
    """
    try:
        from app.services.crawler_service import CrawlerService
        service = CrawlerService(db)
        result = await service.check_login_status(test_page.platform, test_page.url, None)
        
        return {
            "status": "success" if result.get("logged_in") else "failed",
            "message": result.get("message"),
            "data": result
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e),
            "data": None
        }


async def run_crawler_test(test_page: TestPage, db: AsyncSession) -> Dict[str, Any]:
    """
    运行爬虫测试
    """
    try:
        from app.services.crawler_service import CrawlerService
        service = CrawlerService(db)
        
        # 根据平台选择对应的爬虫
        crawler_map = {
            "tonghuashun": service.crawler_map.get("tonghuashun"),
            "wencai": service.crawler_map.get("wencai")
        }
        
        crawler_cls = crawler_map.get(test_page.platform)
        if not crawler_cls:
            return {
                "status": "failed",
                "message": f"Platform {test_page.platform} not supported",
                "data": None
            }
        
        # 实例化爬虫并运行
        crawler = crawler_cls(db)
        
        if test_page.platform == "tonghuashun":
            result = await crawler.crawl()
        elif test_page.platform == "wencai":
            result = await crawler.fetch_and_parse("测试查询")
        else:
            return {
                "status": "failed",
                "message": f"Platform {test_page.platform} not supported",
                "data": None
            }
        
        return {
            "status": "success",
            "message": "Crawler test completed",
            "data": result
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e),
            "data": None
        }