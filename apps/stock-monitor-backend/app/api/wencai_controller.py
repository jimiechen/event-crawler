#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财数据控制器
提供问财数据解析和查询的API接口
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session
from ..services.wencai_service import WencaiService
from ..services.stock_service import StockService
from ..services.pattern_analysis_service import PatternAnalysisService
from ..crawler.wencai_crawler import WencaiCrawler
from .schemas import (
    BaseResponse, ErrorResponse,
    WencaiParseRequest, WencaiParseFileRequest, WencaiParseResponse, WencaiSaveResponse,
    WencaiBatchResponse, WencaiStockResponse,
    WencaiStockData, WencaiValidateRequest, WencaiValidateResponse
)

router = APIRouter(prefix="/api/v1/wencai", tags=["问财数据"])


@router.get("/concepts", response_model=BaseResponse, summary="获取概念云图数据")
async def get_concept_cloud(
    startDate: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    date: Optional[str] = Query(None, description="日期 (兼容旧参数)"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取问财概念云图数据
    包含：概念名称、关联股票数量、平均涨幅、股票列表
    支持日期范围筛选，如果不传日期则默认显示最新的
    """
    try:
        wencai_service = WencaiService(db)
        
        # 兼容旧参数
        if date and not startDate:
            startDate = date
        if date and not endDate:
            endDate = date
            
        concepts = await wencai_service.get_concept_statistics(start_date=startDate, end_date=endDate, keyword=keyword)
        
        return BaseResponse(
            data=concepts,
            message=f"获取概念云图数据成功，共 {len(concepts)} 个概念"
        )
        
    except Exception as e:
        logger.error(f"获取概念云图数据失败: {e}")
        return BaseResponse(
            success=False,
            data=[],
            message=f"获取概念云图数据失败: {str(e)}"
        )


@router.post("/concepts/{concept_name}/hide", response_model=BaseResponse, summary="隐藏概念")
async def hide_concept(
    concept_name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    隐藏指定概念
    """
    try:
        wencai_service = WencaiService(db)
        await wencai_service.hide_concept(concept_name)
        
        return BaseResponse(message=f"概念 '{concept_name}' 已隐藏")
    except Exception as e:
        logger.error(f"隐藏概念失败: {e}")
        return BaseResponse(success=False, message=str(e))

@router.post("/validate", response_model=BaseResponse, summary="问财股票校验")
async def validate_wencai_stock(
    request: WencaiValidateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    校验股票是否符合问财条件
    1. 根据当前日期生成查询条件
    2. 调用爬虫获取结果
    3. 校验股票是否在结果中
    4. 如果在，加入临时股票池
    """
    try:
        logger.info(f"Received validate request: {request}")
        wencai_service = WencaiService(db)
        result = await wencai_service.validate_stock(request.stock_code, request.stock_name)
        
        return BaseResponse(
            success=result["is_valid"],
            data=WencaiValidateResponse(**result),
            message="校验成功" if result["is_valid"] else "校验失败：不符合问财选股条件"
        )
        
    except Exception as e:
        logger.error(f"校验股票失败: {e}")
        return BaseResponse(
            success=False,
            data=None,
            message=f"校验股票失败: {str(e)}"
        )


@router.post("/parse", response_model=BaseResponse, summary="解析HTML内容")
async def parse_html(
    request: WencaiParseRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    解析问财HTML内容
    直接传入HTML字符串进行解析
    """
    try:
        wencai_service = WencaiService(db)
        
        # 创建批次
        batch_id = await wencai_service.create_crawl_batch(
            batch_name=request.batch_name or f"Manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            crawl_url=request.url,
            query_string=request.query
        )
        
        # 解析HTML
        parsed_stocks = wencai_service.parse_html_table(request.html_content)
        
        # 保存结果
        saved_count = 0
        if parsed_stocks:
            await wencai_service.save_stocks(parsed_stocks, batch_id)
            saved_count = len(parsed_stocks)
            
            # 触发后续处理
            await wencai_service.process_batch_data(batch_id)
            await wencai_service.update_batch_status(batch_id, 'completed', saved_count, saved_count, 0)
        else:
            await wencai_service.update_batch_status(batch_id, 'completed', 0, 0, 0, 'No data parsed')
        
        # 构造响应
        response_data = WencaiParseResponse(
            batch_id=batch_id,
            total_records=saved_count,
            success_records=saved_count,
            failed_records=0,
            errors=[],
            parsed_stocks=[WencaiStockData(**stock) for stock in parsed_stocks]
        )
        
        return BaseResponse(
            data=response_data,
            message=f"解析完成，共 {saved_count} 条记录"
        )
        
    except Exception as e:
        logger.error(f"解析HTML失败: {e}")
        return BaseResponse(
            success=False,
            data=None,
            message=f"解析HTML失败: {str(e)}"
        )


@router.post("/parse/file", response_model=BaseResponse, summary="解析HTML文件")
async def parse_html_file(
    batch_name: Optional[str] = Body(None),
    html_content: str = Body(..., media_type="text/html"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    接收上传的HTML文件内容并解析
    """
    try:
        wencai_service = WencaiService(db)
        
        # 创建批次
        batch_id = await wencai_service.create_crawl_batch(
            batch_name=batch_name or f"Upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            crawl_url="file_upload",
            query_string="file_upload"
        )
        
        # 解析HTML
        parsed_stocks = wencai_service.parse_html_table(html_content)
        
        # 保存结果
        total_records = len(parsed_stocks)
        success_count = 0
        failed_count = 0
        errors = []
        
        if parsed_stocks:
            try:
                await wencai_service.save_stocks(parsed_stocks, batch_id)
                success_count = total_records
            except Exception as e:
                logger.error(f"保存股票数据失败: {e}")
                failed_count = total_records
                errors.append(str(e))
        
        # 更新批次状态
        batch_status = 'completed' if failed_count == 0 else 'failed'
        error_msg = '; '.join(errors) if errors else None
        
        await wencai_service.update_batch_status(
            batch_id, 
            batch_status, 
            total_records, 
            success_records=success_count, 
            failed_records=failed_count, 
            error_message=error_msg
        )

        # 触发后续处理流程（解析标签、关联股票等）
        if batch_status == 'completed':
            try:
                await wencai_service.process_batch_data(batch_id)
            except Exception as e:
                logger.error(f"批次 {batch_id} 后续处理失败: {e}")
                # 记录错误但不影响主流程响应
                await wencai_service.update_batch_status(
                    batch_id, 
                    'completed_with_errors', 
                    total_records, 
                    success_records=success_count, 
                    failed_records=failed_count, 
                    error_message=f"数据保存成功但后续处理失败: {str(e)}"
                )

        # 构造响应
        parsed_stocks_response = []
        for stock in parsed_stocks:
            try:
                parsed_stocks_response.append(WencaiStockData(**stock))
            except Exception:
                pass

        response_data = WencaiParseResponse(
            batch_id=batch_id,
            total_records=total_records,
            success_records=success_count,
            failed_records=failed_count,
            errors=errors,
            parsed_stocks=parsed_stocks_response
        )

        return BaseResponse(
            success=batch_status == 'completed',
            data=response_data,
            message=f"HTML保存并解析完成：共 {total_records} 条，成功 {success_count} 条，失败 {failed_count} 条"
        )
        
    except Exception as e:
        logger.error(f"保存HTML文件失败: {e}")
        
        return BaseResponse(
            success=False,
            data=None,
            message=f"保存HTML文件失败: {str(e)}"
        )


@router.get("/batches/dates", response_model=BaseResponse, summary="获取批次日期列表")
async def get_batch_dates(
    db: AsyncSession = Depends(get_db_session)
):
    """获取所有存在的批次日期（query_date）列表"""
    try:
        sql = """
        SELECT DISTINCT query_date 
        FROM wencai_crawl_batches 
        WHERE query_date IS NOT NULL 
        ORDER BY query_date DESC
        """
        
        from sqlalchemy import text
        result = await db.execute(text(sql))
        rows = result.fetchall()
        
        dates = [row[0] for row in rows if row[0]]
        
        return BaseResponse(
            data=dates,
            message=f"获取日期列表成功，共 {len(dates)} 个"
        )
    except Exception as e:
        logger.error(f"获取日期列表失败: {e}")
        return BaseResponse(
            success=False,
            data=[],
            message=f"获取日期列表失败: {str(e)}"
        )


@router.get("/batches", response_model=BaseResponse, summary="获取抓取批次列表")
async def get_crawl_batches(
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    query_date: Optional[str] = Query(None, description="查询日期 (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取问财数据抓取批次列表"""
    try:
        # 构建查询SQL
        where_conditions = []
        params = {'limit': limit, 'offset': offset}
        
        if status_filter:
            where_conditions.append("status = :status")
            params['status'] = status_filter
            
        if start_date:
            where_conditions.append("created_at >= :start_date")
            params['start_date'] = start_date
            
        if end_date:
            where_conditions.append("created_at <= :end_date")
            params['end_date'] = end_date
            
        if query_date:
            where_conditions.append("query_date = :query_date")
            params['query_date'] = query_date
            
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        sql = f"""
        SELECT * FROM wencai_crawl_batches 
        {where_clause}
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
        """
        
        from sqlalchemy import text
        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        
        batches = [dict(row._mapping) for row in rows]
        
        return BaseResponse(
            data=batches,
            message=f"获取批次列表成功，共 {len(batches)} 条"
        )
        
    except Exception as e:
        logger.error(f"获取批次列表失败: {e}")
        
        error_message = "获取批次列表失败"
        if "database" in str(e).lower() or "connection" in str(e).lower():
            error_message = "数据库连接错误，请稍后重试"
        elif "timeout" in str(e).lower():
            error_message = "查询超时，请稍后重试"
        
        return BaseResponse(
            success=False,
            data=[],
            message=error_message
        )


@router.get("/batches/{batch_id}", response_model=BaseResponse, summary="获取批次详情")
async def get_batch_detail(
    batch_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """获取指定批次的详细信息"""
    try:
        wencai_service = WencaiService(db)
        batch_info = await wencai_service.get_batch_info(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"批次不存在: {batch_id}"
            )
        
        return BaseResponse(
            data=batch_info,
            message="获取批次详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批次详情失败: {e}")
        
        error_message = "获取批次详情失败"
        if "database" in str(e).lower() or "connection" in str(e).lower():
            error_message = "数据库连接错误，请稍后重试"
        
        return BaseResponse(
            success=False,
            data=None,
            message=error_message
        )


@router.get("/crawler/{crawl_date}/{crawler_type}", response_model=BaseResponse, summary="按日期执行问财爬虫")
async def run_wencai_crawler_by_date(
    crawl_date: str = Path(..., description="爬取日期 (YYYY-MM-DD)"),
    crawler_type: int = Path(..., description="爬虫类型 (1=问财爬虫)"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    按日期执行问财爬虫
    
    Args:
        crawl_date: 爬取日期，格式为 YYYY-MM-DD
        crawler_type: 爬虫类型，当前只支持 1（问财爬虫）
        db: 数据库会话
    
    Returns:
        爬取结果，包含批次ID、成功数量等信息
    """
    try:
        # 验证爬虫类型
        if crawler_type != 1:
            return BaseResponse(
                success=False,
                data=None,
                message=f"不支持的爬虫类型: {crawler_type}，当前只支持类型 1（问财爬虫）"
            )
        
        # 解析日期
        try:
            target_date = datetime.strptime(crawl_date, "%Y-%m-%d").date()
        except ValueError:
            return BaseResponse(
                success=False,
                data=None,
                message=f"无效的日期格式: {crawl_date}，请使用 YYYY-MM-DD 格式"
            )
        
        # 检查是否为周末
        if target_date.weekday() >= 5:
            return BaseResponse(
                success=False,
                data=None,
                message=f"{crawl_date} 是周末，跳过爬取"
            )
        
        logger.info(f"开始执行问财爬虫，日期: {crawl_date}，类型: {crawler_type}")
        
        # 生成查询条件
        d1 = target_date.strftime("%Y年%m月%d日")
        d2 = (target_date - timedelta(days=1)).strftime("%Y年%m月%d日")
        query = f"{d1}成交量是{d2}成交量的2.5倍以上，非北交 非创业版，非科创版，非ST，概念 行业，{d2}和{d1}涨幅低于13% 收盘价低于25"
        
        logger.info(f"生成的查询条件: {query}")
        
        # 使用wencai_service执行爬取
        from app.crawler.wencai_crawler import WencaiCrawler
        crawler = WencaiCrawler(db)
        
        # 生成批次名称
        batch_name = f"AutoCrawl_{target_date.strftime('%Y%m%d')}"
        
        # 执行爬取
        result = await crawler.fetch_and_parse(
            query=query,
            batch_name=batch_name,
            target_stock_code=None,
            target_date=target_date
        )
        
        logger.info(f"问财爬虫完成: {result}")
        
        return BaseResponse(
            success=result.get("status") == "completed",
            data={
                "batch_id": result.get("batch_id"),
                "total": result.get("total"),
                "success": result.get("success"),
                "crawl_date": crawl_date,
                "crawler_type": crawler_type
            },
            message=f"爬取完成：共 {result.get('total')} 条，成功 {result.get('success')} 条"
        )
        
    except Exception as e:
        logger.error(f"执行问财爬虫失败: {e}")
        return BaseResponse(
            success=False,
            data=None,
            message=f"执行问财爬虫失败: {str(e)}"
        )


@router.post("/batches/{batch_id}/sync_to_pool", response_model=BaseResponse, summary="同步批次股票到监控池")
async def sync_batch_to_pool(
    batch_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    同步指定批次的所有股票到监控池
    同时会自动关联日期标签和"三倍量"标签
    """
    try:
        wencai_service = WencaiService(db)
        result = await wencai_service.sync_batch_stocks_to_pool(batch_id)
        
        return BaseResponse(
            data=result,
            message=f"同步完成：成功 {result['success']}，失败 {result['failed']}"
        )
        
    except Exception as e:
        logger.error(f"同步批次到监控池失败: {e}")
        return BaseResponse(
            success=False,
            data=None,
            message=f"同步失败: {str(e)}"
        )


@router.get("/batches/{batch_id}/dedup_records", response_model=BaseResponse, summary="获取批次去重记录")
async def get_batch_dedup_records(
    batch_id: int,
    limit: int = Query(100, ge=1, le=5000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取指定批次的去重记录（包含所有抓取到的数据，含重复项）"""
    try:
        sql = """
        SELECT * FROM wencai_data_dedup 
        WHERE crawl_batch_id = :batch_id
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
        """
        
        from sqlalchemy import text
        result = await db.execute(text(sql), {'batch_id': batch_id, 'limit': limit, 'offset': offset})
        rows = result.fetchall()
        
        records = [dict(row._mapping) for row in rows]
        
        return BaseResponse(
            data=records,
            message=f"获取批次去重记录成功，共 {len(records)} 条"
        )
        
    except Exception as e:
        logger.error(f"获取批次去重记录失败: {e}")
        return BaseResponse(
            success=False,
            data=[],
            message=f"获取批次去重记录失败: {str(e)}"
        )


@router.get("/stocks", response_model=BaseResponse, summary="获取问财股票数据")
async def get_wencai_stocks(
    batch_id: Optional[int] = Query(None, description="批次ID"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取问财股票数据"""
    try:
        wencai_service = WencaiService(db)
        
        # 兼容旧参数名
        filters = {}
        if batch_id:
            filters['crawl_batch_id'] = batch_id
        if stock_code:
            filters['stock_code'] = stock_code
            
        result = await wencai_service.get_stocks(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return BaseResponse(
            data=result,
            message=f"获取股票数据成功，共 {len(result)} 条"
        )
        
    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")
        return BaseResponse(
            success=False,
            data=[],
            message=f"获取股票数据失败: {str(e)}"
        )
