#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财数据控制器
提供问财数据解析和查询的API接口
"""

from typing import List, Optional
from datetime import datetime
import os
import json
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session
from ..services.wencai_service import WencaiService
from .schemas import (
    BaseResponse, ErrorResponse,
    WencaiParseRequest, WencaiParseFileRequest, WencaiParseResponse, WencaiSaveResponse,
    WencaiBatchResponse, WencaiStockResponse,
    WencaiStockData
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

@router.post("/parse", response_model=BaseResponse, summary="解析并保存问财HTML数据")
async def parse_wencai_data(
    request: WencaiParseRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    保存问财页面HTML文件，并解析入库
    """
    try:
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # 生成一个简单的序号而不是批次ID
        import random
        file_id = random.randint(10, 99)
        html_filename = f"wencai_html_{timestamp}_{file_id}.html"
        
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        html_file_path = os.path.join(project_root, "debug", "html_files", html_filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
        
        # 异步保存HTML文件
        async with aiofiles.open(html_file_path, 'w', encoding='utf-8') as f:
            await f.write(request.html_content)
        
        # 获取文件大小
        file_size = len(request.html_content.encode('utf-8'))
        
        logger.info(f"HTML文件已保存: {html_file_path}, 大小: {file_size} 字节")
        
        # 创建抓取批次
        wencai_service = WencaiService(db)
        batch_name = request.batch_name or f"在线解析_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        batch_id = await wencai_service.create_crawl_batch(
            batch_name=batch_name, 
            crawl_url=request.crawl_url, 
            file_name=html_filename,
            query_string=request.query_string
        )

        # 解析HTML内容
        parsed_stocks = wencai_service.parse_html_table(request.html_content, debug=False)

        if not parsed_stocks:
            await wencai_service.update_batch_status(batch_id, 'failed', 0, 0, 0, '未能解析到有效的股票数据')
            return BaseResponse(
                success=False,
                data=WencaiParseResponse(
                    batch_id=batch_id,
                    total_records=0,
                    success_records=0,
                    failed_records=0,
                    errors=['未能解析到有效的股票数据'],
                    parsed_stocks=[]
                ),
                message="解析失败：未找到有效的股票数据"
            )

        # 保存解析结果
        success_count, failed_count, errors = await wencai_service.save_wencai_stocks(batch_id, parsed_stocks)
        total_records = len(parsed_stocks)
        batch_status = 'completed' if success_count > 0 else 'failed'
        await wencai_service.update_batch_status(batch_id, batch_status, total_records, success_count, failed_count, '; '.join(errors) if errors else None)

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

        if query_date:
            where_conditions.append("query_date = :query_date")
            params['query_date'] = query_date
        
        # 只有在没有指定 query_date 时，才考虑 start_date/end_date (作为 created_at 过滤)
        # 或者两者并存？通常 query_date 更精确。
        # 这里保留 created_at 过滤作为补充
        if start_date:
            where_conditions.append("created_at >= :start_date")
            params['start_date'] = f"{start_date} 00:00:00"
            
        if end_date:
            where_conditions.append("created_at <= :end_date")
            params['end_date'] = f"{end_date} 23:59:59"
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        sql = f"""
        SELECT * FROM wencai_crawl_batches 
        {where_clause}
        ORDER BY started_at DESC 
        LIMIT :limit OFFSET :offset
        """
        
        from sqlalchemy import text
        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        
        batches = [dict(row._mapping) for row in rows]
        
        # 获取这些批次的标签
        if batches:
            batch_ids = [b['id'] for b in batches]
            
            # 1. 查询关联表中的标签 (batch_tag_relations)
            tag_sql = """
            SELECT r.batch_id, t.id, t.name, t.tag_type, t.score
            FROM stock_tags_info t
            JOIN batch_tag_relations r ON t.id = r.tag_id
            WHERE r.batch_id IN :batch_ids
            """
            
            tag_result = await db.execute(text(tag_sql), {'batch_ids': tuple(batch_ids)})
            tag_rows = tag_result.fetchall()
            
            # 构建 batch_id -> tags 映射 (来自关联表)
            relation_tags_map = {}
            for tag_row in tag_rows:
                tag_data = dict(tag_row._mapping)
                b_id = tag_data.pop('batch_id')
                if b_id not in relation_tags_map:
                    relation_tags_map[b_id] = []
                relation_tags_map[b_id].append(tag_data)
            
            # 2. 合并 tags 字段中的标签
            for batch in batches:
                final_tags = []
                seen_tag_names = set()
                
                # 先添加关联表的标签
                rel_tags = relation_tags_map.get(batch['id'], [])
                for tag in rel_tags:
                    if tag['name'] not in seen_tag_names:
                        final_tags.append(tag)
                        seen_tag_names.add(tag['name'])
                
                # 再添加 tags 字段中的标签 (JSON column)
                # 注意：tags 字段可能是字符串(JSON)或已经是对象(取决于驱动)，也可能是 None
                col_tags_raw = batch.get('tags')
                col_tags = []
                
                if col_tags_raw:
                    if isinstance(col_tags_raw, str):
                        try:
                            col_tags = json.loads(col_tags_raw)
                        except json.JSONDecodeError:
                            col_tags = []
                    elif isinstance(col_tags_raw, list):
                        col_tags = col_tags_raw
                
                for tag in col_tags:
                    # 统一字段名: JSON中存的是 type, 前端需要 tag_type
                    tag_name = tag.get('name')
                    if tag_name and tag_name not in seen_tag_names:
                        # 转换结构适配前端
                        new_tag = {
                            'id': tag.get('id'),
                            'name': tag_name,
                            'tag_type': tag.get('type') or tag.get('tag_type'), # 兼容 type 和 tag_type
                            'score': tag.get('score')
                        }
                        final_tags.append(new_tag)
                        seen_tag_names.add(tag_name)
                
                batch['tags'] = final_tags
        
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
    limit: int = Query(100, ge=1, le=5000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取问财股票数据"""
    try:
        # 构建查询SQL
        where_conditions = []
        params = {'limit': limit, 'offset': offset}
        
        if batch_id:
            where_conditions.append("crawl_batch_id = :batch_id")
            params['batch_id'] = batch_id
        
        if stock_code:
            where_conditions.append("stock_code = :stock_code")
            params['stock_code'] = stock_code

        if start_date:
            where_conditions.append("created_at >= :start_date")
            params['start_date'] = f"{start_date} 00:00:00"
            
        if end_date:
            where_conditions.append("created_at <= :end_date")
            params['end_date'] = f"{end_date} 23:59:59"
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        sql = f"""
        SELECT * FROM wencai_stocks 
        {where_clause}
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
        """
        
        from sqlalchemy import text
        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        
        stocks = [dict(row._mapping) for row in rows]
        
        return BaseResponse(
            data=stocks,
            message=f"获取问财股票数据成功，共 {len(stocks)} 条"
        )
        
    except Exception as e:
        logger.error(f"获取问财股票数据失败: {e}")
        
        error_message = "获取问财股票数据失败"
        if "database" in str(e).lower() or "connection" in str(e).lower():
            error_message = "数据库连接错误，请稍后重试"
        elif "timeout" in str(e).lower():
            error_message = "查询超时，请稍后重试"
        elif "invalid" in str(e).lower():
            error_message = "查询参数无效，请检查股票代码或批次ID"
        
        return BaseResponse(
            success=False,
            data=[],
            message=error_message
        )


@router.get("/stocks/latest", response_model=BaseResponse, summary="获取最新问财股票数据")
async def get_latest_wencai_stocks(
    limit: int = Query(100, ge=1, le=5000, description="返回数量限制"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取最新的问财股票数据（每只股票的最新记录）"""
    try:
        wencai_service = WencaiService(db)
        latest_stocks = await wencai_service.get_latest_wencai_stocks(limit)
        
        return BaseResponse(
            data=latest_stocks,
            message=f"获取最新问财股票数据成功，共 {len(latest_stocks)} 条"
        )
        
    except Exception as e:
        logger.error(f"获取最新问财股票数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取最新问财股票数据失败"
        )


@router.get("/stats", response_model=BaseResponse, summary="获取问财数据统计")
async def get_wencai_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取问财数据抓取统计信息"""
    try:
        sql = """
        SELECT 
            DATE(started_at) as crawl_date,
            COUNT(*) as total_batches,
            SUM(total_records) as total_records,
            SUM(success_records) as total_success,
            SUM(failed_records) as total_failed
        FROM wencai_crawl_batches
        WHERE started_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
        GROUP BY DATE(started_at)
        ORDER BY crawl_date DESC
        """
        
        from sqlalchemy import text
        from decimal import Decimal
        
        result = await db.execute(text(sql), {'days': days})
        rows = result.fetchall()
        
        stats = []
        for row in rows:
            row_dict = dict(row._mapping)
            # 计算成功率，处理Decimal类型
            total_records = row_dict.get('total_records', 0)
            success_records = row_dict.get('total_success', 0)
            
            if total_records and total_records > 0:
                # 确保类型转换正确
                success_rate = float(success_records) * 100.0 / float(total_records)
                row_dict['avg_success_rate'] = round(success_rate, 2)
            else:
                row_dict['avg_success_rate'] = 0.0
            
            stats.append(row_dict)
        
        # 计算总体统计
        total_batches = sum(int(row.get('total_batches', 0)) for row in stats)
        total_records = sum(int(row.get('total_records', 0)) for row in stats)
        total_success = sum(int(row.get('total_success', 0)) for row in stats)
        total_failed = sum(int(row.get('total_failed', 0)) for row in stats)
        
        total_stats = {
            'total_batches': total_batches,
            'total_records': total_records,
            'total_success': total_success,
            'total_failed': total_failed,
            'daily_stats': stats
        }
        
        if total_records > 0:
            total_stats['overall_success_rate'] = round(
                float(total_success) * 100.0 / float(total_records), 2
            )
        else:
            total_stats['overall_success_rate'] = 0.0
        
        return BaseResponse(
            data=total_stats,
            message=f"获取最近 {days} 天问财数据统计成功"
        )
        
    except Exception as e:
        logger.error(f"获取问财数据统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取问财数据统计失败"
        )


@router.delete("/stocks/{stock_code}", response_model=BaseResponse, summary="删除问财股票")
async def delete_wencai_stock(
    stock_code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """删除指定的问财股票及其相关数据"""
    try:
        # 删除相关数据
        from sqlalchemy import text
        
        # 删除股票数据
        result = await db.execute(
            text("DELETE FROM wencai_stocks WHERE stock_code = :stock_code"),
            {'stock_code': stock_code}
        )
        deleted_stocks = result.rowcount
        
        # 删除去重记录
        result = await db.execute(
            text("DELETE FROM wencai_data_dedup WHERE stock_code = :stock_code"),
            {'stock_code': stock_code}
        )
        
        await db.commit()
        
        if deleted_stocks == 0:
             return BaseResponse(
                success=True, # Return true even if not found to be idempotent
                data={'deleted_stock_code': stock_code, 'count': 0},
                message=f"未找到股票 {stock_code}"
            )

        return BaseResponse(
            data={'deleted_stock_code': stock_code, 'count': deleted_stocks},
            message=f"股票 {stock_code} 删除成功"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"删除股票失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除股票失败"
        )


@router.delete("/batches/{batch_id}", response_model=BaseResponse, summary="删除抓取批次")
async def delete_crawl_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """删除指定的抓取批次及其相关数据"""
    try:
        # 检查批次是否存在
        wencai_service = WencaiService(db)
        batch_info = await wencai_service.get_batch_info(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"批次不存在: {batch_id}"
            )
        
        # 删除相关数据
        from sqlalchemy import text
        
        # 删除股票数据
        await db.execute(
            text("DELETE FROM wencai_stocks WHERE crawl_batch_id = :batch_id"),
            {'batch_id': batch_id}
        )
        
        # 删除去重记录
        await db.execute(
            text("DELETE FROM wencai_data_dedup WHERE crawl_batch_id = :batch_id"),
            {'batch_id': batch_id}
        )
        
        # 删除批次记录
        await db.execute(
            text("DELETE FROM wencai_crawl_batches WHERE id = :batch_id"),
            {'batch_id': batch_id}
        )
        
        await db.commit()
        
        return BaseResponse(
            data={'deleted_batch_id': batch_id},
            message=f"批次 {batch_id} 及其相关数据删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除批次失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除批次失败"
        )


@router.post("/parse-file", response_model=BaseResponse, summary="解析HTML文件")
async def parse_wencai_file(
    request: WencaiParseFileRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    读取本地HTML文件并解析问财数据
    
    Args:
        request: 包含文件路径和批次信息的请求
        db: 数据库会话
        
    Returns:
        解析结果，包含详细的调试信息
    """
    try:
        wencai_service = WencaiService(db)
        
        # 处理文件路径
        file_path = request.file_path
        
        # 如果只提供了文件名，则在debug目录中查找
        if not os.path.isabs(file_path):
            # 获取项目根目录路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            debug_dir = os.path.join(project_root, "debug", "html_files")
            file_path = os.path.join(debug_dir, file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return BaseResponse(
                success=False,
                data=None,
                message=f"文件不存在: {file_path}"
            )
        
        # 读取HTML文件内容
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                html_content = await f.read()
            
            logger.info(f"成功读取HTML文件: {file_path}, 文件大小: {len(html_content)} 字符")
        except Exception as e:
            logger.error(f"读取HTML文件失败: {e}")
            return BaseResponse(
                success=False,
                data=None,
                message=f"读取文件失败: {str(e)}"
            )
        
        # 生成批次名称
        batch_name = request.batch_name or f"文件解析测试_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 提取文件名用于索引
        file_name = os.path.basename(file_path)
        
        # 创建抓取批次，传递文件名用于索引
        batch_id = await wencai_service.create_crawl_batch(batch_name, request.crawl_url or file_path, file_name)
        
        # 解析HTML数据（带详细调试信息）
        logger.info(f"开始解析HTML文件数据，批次ID: {batch_id}, 文件: {file_path}")
        parsed_stocks = wencai_service.parse_html_table(html_content, debug=True)
        
        if not parsed_stocks:
            # 更新批次状态为失败
            await wencai_service.update_batch_status(
                batch_id, 'failed', 0, 0, 0, '未能解析到有效的股票数据'
            )
            
            return BaseResponse(
                success=False,
                data=WencaiParseResponse(
                    batch_id=batch_id,
                    total_records=0,
                    success_records=0,
                    failed_records=0,
                    errors=['未能解析到有效的股票数据'],
                    parsed_stocks=[]
                ),
                message=f"解析失败：未找到有效的股票数据 (文件: {os.path.basename(file_path)})"
            )
        
        # 保存股票数据
        logger.info(f"开始保存 {len(parsed_stocks)} 条股票数据")
        success_count, failed_count, errors = await wencai_service.save_wencai_stocks(
            batch_id, parsed_stocks
        )
        
        # 更新批次状态
        total_records = len(parsed_stocks)
        batch_status = 'completed' if success_count > 0 else 'failed'
        error_message = '; '.join(errors) if errors else None
        
        await wencai_service.update_batch_status(
            batch_id, batch_status, total_records, success_count, failed_count, error_message
        )
        
        # 转换解析的股票数据为响应格式
        parsed_stocks_response = []
        for stock in parsed_stocks:  # 返回所有解析的数据用于调试
            try:
                parsed_stocks_response.append(WencaiStockData(**stock))
            except Exception as e:
                logger.warning(f"转换股票数据失败: {e}")
        
        response_data = WencaiParseResponse(
            batch_id=batch_id,
            total_records=total_records,
            success_records=success_count,
            failed_records=failed_count,
            errors=errors,
            parsed_stocks=parsed_stocks_response
        )
        
        message = f"文件解析完成：{os.path.basename(file_path)} - 总计 {total_records} 条，成功 {success_count} 条，失败 {failed_count} 条"
        
        return BaseResponse(
            success=batch_status == 'completed',
            data=response_data,
            message=message
        )
        
    except Exception as e:
        logger.error(f"解析HTML文件失败: {e}")
        
        error_message = f"解析HTML文件失败: {str(e)}"
        
        return BaseResponse(
            success=False,
            data=None,
            message=error_message
        )
