#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据合并API控制器
提供数据合并、去重、CSV更新等接口
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from loguru import logger

from app.database import get_db_session
from app.services.data_merge_service import DataMergeService
from app.api.schemas import BaseResponse as ResponseModel

router = APIRouter(prefix="/data-merge", tags=["数据合并"])


class MergeRequest(BaseModel):
    """合并请求"""
    csv_file_path: str = Field(..., description="CSV文件路径")
    date_column: str = Field(default="trade_date", description="日期列名")
    code_column: str = Field(default="code", description="股票代码列名")
    keep_latest: bool = Field(default=True, description="是否保留最新数据")
    update_csv: bool = Field(default=True, description="是否更新CSV文件")


class TushareMergeRequest(BaseModel):
    """Tushare合并请求"""
    data: List[dict] = Field(..., description="Tushare数据列表")
    keep_latest: bool = Field(default=True, description="是否保留最新数据")
    csv_file_path: Optional[str] = Field(None, description="CSV文件路径（可选）")


class AkshareMergeRequest(BaseModel):
    """akshare合并请求"""
    data: List[dict] = Field(..., description="akshare数据列表")
    keep_latest: bool = Field(default=True, description="是否保留最新数据")
    csv_file_path: Optional[str] = Field(None, description="CSV文件路径（可选）")


class DeduplicateRequest(BaseModel):
    """去重请求"""
    code: Optional[str] = Field(None, description="股票代码（可选）")
    start_date: Optional[date] = Field(None, description="开始日期（可选）")
    end_date: Optional[date] = Field(None, description="结束日期（可选）")


class UpdateCsvRequest(BaseModel):
    """更新CSV请求"""
    csv_file_path: str = Field(..., description="CSV文件路径")
    date_column: str = Field(default="trade_date", description="日期列名")
    code_column: str = Field(default="code", description="股票代码列名")
    start_date: Optional[date] = Field(None, description="开始日期（可选）")
    end_date: Optional[date] = Field(None, description="结束日期（可选）")


@router.post("/csv", response_model=ResponseModel)
async def merge_csv(
    request: MergeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    合并CSV文件到数据库
    
    - 支持按日期去重
    - 保留最新数据
    - 自动更新CSV文件
    """
    try:
        service = DataMergeService(db)
        result = await service.merge_csv_to_database(
            csv_file_path=request.csv_file_path,
            date_column=request.date_column,
            code_column=request.code_column,
            keep_latest=request.keep_latest,
            update_csv=request.update_csv
        )
        
        return ResponseModel(
            success=True,
            message="CSV文件合并成功",
            data=result
        )
    except FileNotFoundError as e:
        logger.error(f"CSV文件不存在: {e}")
        return ResponseModel(
            success=False,
            message=f"CSV文件不存在: {str(e)}"
        )
    except Exception as e:
        logger.error(f"合并CSV文件失败: {e}")
        return ResponseModel(
            success=False,
            message=f"合并失败: {str(e)}"
        )


@router.post("/tushare", response_model=ResponseModel)
async def merge_tushare(
    request: TushareMergeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    合并Tushare数据到数据库
    
    - 支持按日期去重
    - 保留最新数据
    - 可选更新CSV文件
    """
    try:
        service = DataMergeService(db)
        result = await service.merge_tushare_data(
            tushare_data=request.data,
            keep_latest=request.keep_latest,
            csv_file_path=request.csv_file_path
        )
        
        return ResponseModel(
            success=True,
            message="Tushare数据合并成功",
            data=result
        )
    except Exception as e:
        logger.error(f"合并Tushare数据失败: {e}")
        return ResponseModel(
            success=False,
            message=f"合并失败: {str(e)}"
        )


@router.post("/akshare", response_model=ResponseModel)
async def merge_akshare(
    request: AkshareMergeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    合并akshare数据到数据库
    
    - 支持按日期去重
    - 保留最新数据
    - 可选更新CSV文件
    """
    try:
        service = DataMergeService(db)
        result = await service.merge_akshare_data(
            akshare_data=request.data,
            keep_latest=request.keep_latest,
            csv_file_path=request.csv_file_path
        )
        
        return ResponseModel(
            success=True,
            message="akshare数据合并成功",
            data=result
        )
    except Exception as e:
        logger.error(f"合并akshare数据失败: {e}")
        return ResponseModel(
            success=False,
            message=f"合并失败: {str(e)}"
        )


@router.post("/deduplicate", response_model=ResponseModel)
async def deduplicate_by_date(
    request: DeduplicateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    按日期去重，保留最新数据
    
    - 可以指定股票代码范围
    - 可以指定日期范围
    - 自动删除重复记录
    """
    try:
        service = DataMergeService(db)
        result = await service.deduplicate_by_date(
            code=request.code,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return ResponseModel(
            success=True,
            message="去重成功",
            data=result
        )
    except Exception as e:
        logger.error(f"去重失败: {e}")
        return ResponseModel(
            success=False,
            message=f"去重失败: {str(e)}"
        )


@router.post("/update-csv", response_model=ResponseModel)
async def update_csv_from_database(
    request: UpdateCsvRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    从数据库更新CSV文件
    
    - 可以指定日期范围
    - 自动覆盖CSV文件
    """
    try:
        service = DataMergeService(db)
        result = await service.update_csv_from_database(
            csv_file_path=request.csv_file_path,
            date_column=request.date_column,
            code_column=request.code_column,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return ResponseModel(
            success=True,
            message="CSV文件更新成功",
            data=result
        )
    except Exception as e:
        logger.error(f"更新CSV文件失败: {e}")
        return ResponseModel(
            success=False,
            message=f"更新失败: {str(e)}"
        )


@router.post("/upload-csv", response_model=ResponseModel)
async def upload_and_merge_csv(
    file: UploadFile = File(...),
    date_column: str = Query(default="trade_date", description="日期列名"),
    code_column: str = Query(default="code", description="股票代码列名"),
    keep_latest: bool = Query(default=True, description="是否保留最新数据"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    上传CSV文件并合并到数据库
    
    - 支持文件上传
    - 自动解析CSV
    - 合并到数据库
    """
    try:
        import tempfile
        import os
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 合并CSV文件
            service = DataMergeService(db)
            result = await service.merge_csv_to_database(
                csv_file_path=temp_file_path,
                date_column=date_column,
                code_column=code_column,
                keep_latest=keep_latest,
                update_csv=False  # 不更新临时文件
            )
            
            return ResponseModel(
                success=True,
                message="CSV文件上传并合并成功",
                data=result
            )
        finally:
            # 删除临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"上传并合并CSV文件失败: {e}")
        return ResponseModel(
            success=False,
            message=f"上传失败: {str(e)}"
        )


@router.get("/{stock_code}", response_model=ResponseModel)
@router.post("/{stock_code}", response_model=ResponseModel)
async def merge_stock_data_smart(
    stock_code: str,
    source: Optional[str] = Query(None, description="数据源（可选：csv/tushare/akshare）"),
    target_date: Optional[str] = Query(None, description="目标日期（YYYYMMDD或YYYY-MM-DD）"),
    force_sync: bool = Query(False, description="强制同步（忽略日期检查）"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    智能数据合并接口
    
    - 股票代码作为路径参数
    - 支持GET和POST请求
    - 自动判断需要同步的日期
    - 避免重复数据
    - 数据一致性校验
    - 支持指定日期补全数据
    """
    try:
        service = DataMergeService(db)
        result = await service.merge_stock_smart(
            stock_code=stock_code,
            source=source,
            target_date=target_date,
            force_sync=force_sync
        )
        
        message = f"股票 {stock_code} "
        if result.get('synced', True):
            message += f"同步成功: {result.get('merged', 0)} 条"
        else:
            message += result.get('message', '处理完成')
        
        return ResponseModel(
            success=True,
            message=message,
            data=result
        )
    except Exception as e:
        logger.error(f"智能合并股票 {stock_code} 数据失败: {e}")
        return ResponseModel(
            success=False,
            message=f"合并失败: {str(e)}"
        )
