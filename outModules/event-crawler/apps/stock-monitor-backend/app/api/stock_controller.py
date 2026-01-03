#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据控制器
提供股票信息和股票数据的API接口
"""

from typing import List, Optional
from datetime import datetime, timedelta
import json
import re
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session, db_manager
from ..services.stock_service import StockService
from ..services.tushare_service import TushareService
from ..services.tdx_service import TdxService
from ..repositories.stock_repository import TonghuashunRawLogRepository
from .schemas import (
    BaseResponse, ErrorResponse, ListResponse,
    StockInfoCreate, StockInfoUpdate, StockInfoResponse,
    StockDataCreate, StockDataBatchCreate, StockDataResponse,
    StockDataQuery, BatchSubmitResponse, StockStatisticsResponse,
    StockListQuery, PaginationParams
)

router = APIRouter(prefix="/api/v1/stocks", tags=["股票数据"])


async def parse_jsonp_response(response_data: str) -> Optional[dict]:
    """
    解析JSONP格式的响应数据
    
    Args:
        response_data: JSONP格式的响应字符串，如 "multimarketreal({...})"
        
    Returns:
        解析后的JSON数据，如果解析失败返回None
    """
    try:
        if not response_data or not isinstance(response_data, str):
            logger.warning(f"无效的响应数据类型: {type(response_data)}")
            return None
        
        # 使用正则表达式提取JSONP中的JSON部分
        # 匹配 multimarketreal({...}) 格式
        jsonp_pattern = r'multimarketreal\s*\(\s*({.*})\s*\)'
        match = re.search(jsonp_pattern, response_data, re.DOTALL)
        
        if not match:
            logger.warning(f"未找到multimarketreal JSONP格式数据")
            logger.debug(f"响应数据前100字符: {response_data[:100]}")
            return None
        
        # 提取JSON字符串
        json_str = match.group(1)
        
        # 解析JSON
        parsed_data = json.loads(json_str)
        logger.info(f"成功解析JSONP数据，包含 {len(parsed_data.get('hs', {}))} 只股票")
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.debug(f"JSON字符串: {json_str[:200] if 'json_str' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"JSONP解析失败: {e}")
        logger.debug(f"响应数据: {response_data[:200] if response_data else 'N/A'}")
        return None


@router.get("/{code}/risk", summary="获取股票风险数据")
async def get_stock_risk(
    code: str,
    db: AsyncSession = Depends(get_db_session)
):
    from ..models.stock import StockTdxRisk
    from .schemas import StockTdxRiskResponse
    from sqlalchemy import select, desc
    
    try:
        # Get latest risk data
        stmt = select(StockTdxRisk).where(
            StockTdxRisk.stock_code == code
        ).order_by(desc(StockTdxRisk.date)).limit(1)
        
        result = await db.execute(stmt)
        risk_data = result.scalar_one_or_none()
        
        # If not found, try to fetch
        if not risk_data:
            tdx_service = TdxService(db)
            risk_data = await tdx_service.store_stock_risk(code)
            
        if not risk_data:
            return BaseResponse(
                code=404,
                message="未找到风险数据",
                data=None
            )
            
        return BaseResponse(
            data=StockTdxRiskResponse.model_validate(risk_data),
            message="获取风险数据成功"
        )
    except Exception as e:
        logger.error(f"获取风险数据失败: {e}")
        return BaseResponse(
            code=500,
            message=f"获取风险数据失败: {str(e)}",
            data=None
        )


@router.post("/info", response_model=BaseResponse, summary="创建股票信息")
async def create_stock_info(
    stock_data: StockInfoCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """创建股票基本信息"""
    try:
        # Tushare 接口调用次数有限，暂时移除自动获取名称功能
        # 如果股票名称为空，前端应强制用户输入或使用默认值
        
        stock_service = StockService(db)
        stock_info = await stock_service.create_or_update_stock_info(stock_data.dict())
        
        # 尝试获取TDX风险数据
        try:
            tdx_service = TdxService(db)
            await tdx_service.store_stock_risk(stock_data.stock_code, stock_data.stock_name)
        except Exception as e:
            logger.warning(f"Failed to update TDX risk data: {e}")
        
        return BaseResponse(
            data=StockInfoResponse.from_orm(stock_info),
            message="股票信息创建成功"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建股票信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建股票信息失败"
        )


@router.get("/info/{stock_code}", response_model=BaseResponse, summary="获取股票信息")
async def get_stock_info(
    stock_code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取股票基本信息"""
    try:
        stock_service = StockService(db)
        stock_info = await stock_service.get_stock_info(stock_code)
        
        if not stock_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"股票不存在: {stock_code}"
            )
        
        return BaseResponse(
            data=StockInfoResponse.from_orm(stock_info),
            message="获取股票信息成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票信息失败"
        )


@router.put("/info/{stock_code}", response_model=BaseResponse, summary="更新股票信息")
async def update_stock_info(
    stock_code: str,
    update_data: StockInfoUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """更新股票基本信息"""
    try:
        stock_service = StockService(db)
        
        # 直接调用 create_or_update_stock_info，如果不存在则创建，如果存在则更新
        # 移除显式的 404 检查，让 service 层处理创建逻辑
        
        # 更新股票信息
        update_dict = update_data.dict(exclude_unset=True)
        update_dict['stock_code'] = stock_code
        stock_info = await stock_service.create_or_update_stock_info(update_dict)
        
        return BaseResponse(
            data=StockInfoResponse.from_orm(stock_info),
            message="股票信息更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新股票信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新股票信息失败"
        )


@router.get("/info", response_model=BaseResponse, summary="获取股票列表")
async def get_stock_list(
    market: Optional[str] = Query(None, description="市场代码"),
    active_only: bool = Query(True, description="仅活跃股票"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取股票列表"""
    try:
        stock_service = StockService(db)
        stocks = await stock_service.get_stock_list(
            market=market,
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        
        # 转换为响应格式
        stock_responses = [StockInfoResponse.from_orm(stock) for stock in stocks]
        
        # 获取总数（简化处理，实际应该单独查询）
        total = len(stock_responses)
        has_more = len(stock_responses) == limit
        
        list_response = ListResponse(
            items=stock_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
        return BaseResponse(
            data=list_response,
            message="获取股票列表成功"
        )
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票列表失败"
        )


@router.post("/data", response_model=BaseResponse, summary="提交股票数据")
async def submit_stock_data(
    stock_data: StockDataCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """提交单条股票数据"""
    try:
        stock_service = StockService(db)
        result = await stock_service.submit_stock_data([stock_data.dict()])
        
        if result['failed'] > 0:
            return BaseResponse(
                success=False,
                data=result,
                message=f"提交失败: {result['errors'][0] if result['errors'] else '未知错误'}"
            )
        
        return BaseResponse(
            data=result,
            message="股票数据提交成功"
        )
    except Exception as e:
        logger.error(f"提交股票数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提交股票数据失败"
        )


@router.post("/data/batch", response_model=BaseResponse, summary="批量提交股票数据")
async def submit_stock_data_batch(
    batch_data: StockDataBatchCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """批量提交股票数据"""
    try:
        stock_service = StockService(db)
        data_list = [item.dict() for item in batch_data.data_list]
        result = await stock_service.submit_stock_data(data_list)
        
        response_data = BatchSubmitResponse(**result)
        
        return BaseResponse(
            data=response_data,
            message=f"批量提交完成: 成功{result['success']}条, 失败{result['failed']}条, 重复{result['duplicated']}条"
        )
    except Exception as e:
        logger.error(f"批量提交股票数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量提交股票数据失败"
        )


@router.get("/data/{stock_code}", response_model=BaseResponse, summary="获取股票数据")
async def get_stock_data(
    stock_code: str,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取股票数据"""
    try:
        stock_service = StockService(db)
        
        # 设置默认时间范围
        if not start_time:
            start_time = datetime.now() - timedelta(days=30)
        if not end_time:
            end_time = datetime.now()
        
        stock_data_list = await stock_service.get_stock_data(
            stock_code=stock_code,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # 转换为响应格式
        data_responses = [StockDataResponse.from_orm(data) for data in stock_data_list]
        
        return BaseResponse(
            data=data_responses,
            message=f"获取股票数据成功，共{len(data_responses)}条"
        )
    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票数据失败"
        )


@router.get("/data/{stock_code}/latest", response_model=BaseResponse, summary="获取最新股票数据")
async def get_latest_stock_data(
    stock_code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取最新股票数据"""
    try:
        stock_service = StockService(db)
        latest_data = await stock_service.get_latest_stock_data(stock_code)
        
        if not latest_data:
            return BaseResponse(
                data=None,
                message=f"暂无股票数据: {stock_code}"
            )
        
        return BaseResponse(
            data=StockDataResponse.from_orm(latest_data),
            message="获取最新股票数据成功"
        )
    except Exception as e:
        logger.error(f"获取最新股票数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取最新股票数据失败"
        )


@router.get("/data/{stock_code}/recent", response_model=BaseResponse, summary="获取最近股票数据")
async def get_recent_stock_data(
    stock_code: str,
    hours: int = Query(24, ge=1, le=168, description="最近小时数"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取最近的股票数据"""
    try:
        stock_service = StockService(db)
        recent_data = await stock_service.get_recent_stock_data(stock_code, hours)
        
        # 转换为响应格式
        data_responses = [StockDataResponse.from_orm(data) for data in recent_data]
        
        return BaseResponse(
            data=data_responses,
            message=f"获取最近{hours}小时股票数据成功，共{len(data_responses)}条"
        )
    except Exception as e:
        logger.error(f"获取最近股票数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取最近股票数据失败"
        )


@router.get("/statistics/{stock_code}", response_model=BaseResponse, summary="获取股票统计信息")
async def get_stock_statistics(
    stock_code: str,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取股票统计信息"""
    try:
        stock_service = StockService(db)
        stats = await stock_service.get_stock_statistics(stock_code, days)
        
        return BaseResponse(
            data=stats,
            message="获取股票统计信息成功"
        )
    except Exception as e:
        logger.error(f"获取股票统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票统计信息失败"
        )


@router.post("/data/cleanup", response_model=BaseResponse, summary="清理旧数据")
async def cleanup_old_data(
    days: int = Query(90, ge=30, le=365, description="保留天数"),
    db: AsyncSession = Depends(get_db_session)
):
    """清理旧的股票数据"""
    try:
        stock_service = StockService(db)
        deleted_count = await stock_service.cleanup_old_data(days)
        
        return BaseResponse(
            data={'deleted_count': deleted_count},
            message=f"清理完成，删除了{deleted_count}条旧数据"
        )
    except Exception as e:
        logger.error(f"清理旧数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理旧数据失败"
        )


@router.get("/search", response_model=BaseResponse, summary="搜索股票")
async def search_stocks(
    q: str = Query(..., description="搜索关键词（股票代码或名称）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(100, ge=1, le=500, description="每页数量"),
    db: AsyncSession = Depends(get_db_session)
):
    """搜索股票（支持股票代码和名称模糊匹配）"""
    try:
        stock_service = StockService(db)
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 执行搜索
        stocks = await stock_service.search_stocks(
            keyword=q,
            limit=size,
            offset=offset
        )
        
        # 转换为响应格式，包含股票信息和最新价格数据
        stock_responses = []
        for stock in stocks:
            # 获取最新价格数据
            latest_data = await stock_service.get_latest_stock_data(stock.symbol)
            
            stock_dict = {
                'code': stock.symbol,
                'symbol': stock.symbol,
                'name': stock.name or stock.symbol,
                'market': stock.market,
                'status': stock.status,
                'price': float(latest_data.price) if latest_data else 0,
                'close_price': float(latest_data.price) if latest_data else 0,
                'open_price': float(latest_data.open_price) if latest_data else 0,
                'high_price': float(latest_data.high) if latest_data else 0,
                'low_price': float(latest_data.low) if latest_data else 0,
                'volume': latest_data.volume if latest_data else 0,
                'amount': float(latest_data.turnover) if latest_data else 0,
                'change_percent': float(latest_data.change_percent) if latest_data else 0,
                'trade_date': latest_data.timestamp if latest_data else None,
                'updated_at': latest_data.created_at if latest_data else stock.updated_at
            }
            stock_responses.append(stock_dict)
        
        return BaseResponse(
            data=stock_responses,
            message=f"搜索完成，找到 {len(stock_responses)} 条结果"
        )
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索股票失败"
        )


@router.post("/{stock_code}/toggle-status", response_model=BaseResponse, summary="切换股票状态")
async def toggle_stock_status(
    stock_code: str,
    is_active: bool = Query(..., description="是否激活"),
    db: AsyncSession = Depends(get_db_session)
):
    """切换股票状态 (激活/停用)"""
    try:
        stock_service = StockService(db)
        await stock_service.toggle_stock_status(stock_code, is_active)
        return BaseResponse(
            message=f"股票 {stock_code} 状态已切换为 {'激活' if is_active else '停用'}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"切换股票状态失败: {e}")
        raise HTTPException(status_code=500, detail="切换股票状态失败")


@router.post("/{stock_code}/move-to-wencai", response_model=BaseResponse, summary="移动到问财表")
async def move_to_wencai(
    stock_code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """将股票移动到问财股票表"""
    try:
        stock_service = StockService(db)
        await stock_service.move_to_wencai(stock_code)
        return BaseResponse(
            message=f"股票 {stock_code} 已成功移动到问财表"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"移动股票到问财表失败: {e}")
        raise HTTPException(status_code=500, detail="移动股票到问财表失败")


@router.post("/wencai/{wencai_id}/move-to-stock-info", response_model=BaseResponse, summary="从问财移动到股票表")
async def move_to_stock_info(
    wencai_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """将股票从问财表移动到股票信息表"""
    try:
        stock_service = StockService(db)
        await stock_service.move_to_stock_info(wencai_id)
        return BaseResponse(
            message=f"问财记录 {wencai_id} 已成功移动到股票信息表"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"移动问财股票到股票信息表失败: {e}")
        raise HTTPException(status_code=500, detail="移动问财股票到股票信息表失败")


@router.get("", response_model=BaseResponse, summary="获取股票列表")
async def get_stocks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(100, ge=1, le=500, description="每页数量"),
    market: Optional[str] = Query(None, description="市场代码"),
    active_only: bool = Query(True, description="仅活跃股票"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取股票列表（用于HTML页面显示）"""
    try:
        stock_service = StockService(db)
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 获取股票列表
        stocks = await stock_service.get_stock_list(
            market=market,
            active_only=active_only,
            limit=size,
            offset=offset
        )
        
        # 转换为响应格式，包含股票信息和最新价格数据
        stock_responses = []
        for stock in stocks:
            # 获取最新价格数据
            latest_data = await stock_service.get_latest_stock_data(stock.symbol)
            
            stock_dict = {
                'code': stock.symbol,
                'symbol': stock.symbol,
                'name': stock.name or stock.symbol,
                'market': stock.market,
                'status': stock.status,
                'price': float(latest_data.price) if latest_data else 0,
                'close_price': float(latest_data.price) if latest_data else 0,
                'open_price': float(latest_data.open_price) if latest_data else 0,
                'high_price': float(latest_data.high) if latest_data else 0,
                'low_price': float(latest_data.low) if latest_data else 0,
                'volume': latest_data.volume if latest_data else 0,
                'amount': float(latest_data.turnover) if latest_data else 0,
                'change_percent': float(latest_data.change_percent) if latest_data else 0,
                'trade_date': latest_data.timestamp if latest_data else None,
                'updated_at': latest_data.created_at if latest_data else stock.updated_at
            }
            stock_responses.append(stock_dict)
        
        return BaseResponse(
            data=stock_responses,
            message=f"获取股票列表成功，共 {len(stock_responses)} 条记录"
        )
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票列表失败"
        )


@router.post("/data/batch-latest", response_model=BaseResponse, summary="批量获取最新数据")
async def batch_get_latest_data(
    stock_codes: List[str],
    db: AsyncSession = Depends(get_db_session)
):
    """批量获取最新股票数据"""
    try:
        if len(stock_codes) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="股票代码数量不能超过100个"
            )
        
        stock_service = StockService(db)
        result = await stock_service.batch_get_latest_data(stock_codes)
        
        # 转换为响应格式
        response_data = {}
        for code, data in result.items():
            if data:
                response_data[code] = StockDataResponse.from_orm(data).dict()
            else:
                response_data[code] = None
        
        return BaseResponse(
            data=response_data,
            message=f"批量获取最新数据成功，共{len(stock_codes)}只股票"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量获取最新数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量获取最新数据失败"
        )


@router.delete("/test-data/clear", response_model=BaseResponse, summary="清空测试数据")
async def clear_test_data(
    db: AsyncSession = Depends(get_db_session)
):
    """清空所有测试数据"""
    try:
        stock_service = StockService(db)
        result = await stock_service.clear_test_data()
        
        return BaseResponse(
            data={
                'success': result['success'],
                'deleted_stock_data': result['deleted_stock_data'],
                'deleted_dedup_logs': result['deleted_dedup_logs'],
                'deleted_tonghuashun_data': result['deleted_tonghuashun_data']
            },
            message=f"清空测试数据成功，删除了 {result['deleted_stock_data']} 条股票数据，{result['deleted_dedup_logs']} 条去重日志，{result['deleted_tonghuashun_data']} 条同花顺数据"
        )
    except Exception as e:
        logger.error(f"清空测试数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清空测试数据失败"
        )


@router.get("/tonghuashun/raw-data", response_model=BaseResponse, summary="获取同花顺股票数据")
async def get_tonghuashun_stock_data(
    limit: int = Query(1000, ge=1, le=5000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    request_timestamp: Optional[str] = Query(None, description="指定时间戳查询"),
    start_timestamp: Optional[str] = Query(None, description="时间戳范围查询开始"),
    end_timestamp: Optional[str] = Query(None, description="时间戳范围查询结束"),
    stock_code: Optional[str] = Query(None, description="股票代码或名称过滤"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取所有同花顺股票数据"""
    try:
        stock_service = StockService(db)
        stock_data_list, total_count = await stock_service.get_all_stock_data(
            limit=limit,
            offset=offset,
            request_timestamp=request_timestamp,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            stock_code=stock_code
        )
        
        # 转换为响应格式
        data_list = []
        for stock_data in stock_data_list:
            # 计算涨跌额
            change_amount = 0
            if stock_data.get('price') and stock_data.get('change_percent'):
                try:
                    price = float(stock_data['price'])
                    change_percent = float(stock_data['change_percent'])
                    change_amount = price * change_percent / 100
                except (ValueError, TypeError):
                    change_amount = 0
            
            data_list.append({
                # 前端期望的字段名
                'symbol': stock_data.get('code'),  # 股票代码
                'name': stock_data.get('stock_name', '未知'),  # 股票名称
                'current_price': float(stock_data.get('price', 0)),  # 当前价格
                'change_amount': round(change_amount, 2),  # 涨跌额
                'volume': stock_data.get('volume', 0),  # 成交量
                'turnover': float(stock_data.get('turnover', 0)),  # 成交额
                'change_percent': float(stock_data.get('change_percent', 0)),  # 涨跌幅
                'high': float(stock_data.get('high', 0)),  # 最高价
                'low': float(stock_data.get('low', 0)),  # 最低价
                'open_price': float(stock_data.get('open_price', 0)),  # 开盘价
                'prev_close': float(stock_data.get('prev_close', 0)),  # 昨收价
                'amplitude': float(stock_data.get('amplitude', 0)),  # 振幅
                'turnover_rate': float(stock_data.get('turnover_rate', 0)),  # 换手率
                'pe_ratio': float(stock_data.get('pe_ratio', 0)),  # 市盈率
                'market_cap': float(stock_data.get('market_cap', 0)),  # 总市值
                'timestamp': stock_data.get('timestamp').isoformat() if stock_data.get('timestamp') else None,
                'request_timestamp': stock_data.get('request_timestamp'),
                'created_at': stock_data.get('created_at').isoformat() if stock_data.get('created_at') else None,
                
                # 保持向后兼容的字段名
                'stock_code': stock_data.get('code'),
                'stock_name': stock_data.get('stock_name', '未知'),
                'price': float(stock_data.get('price', 0))
            })
        
        return BaseResponse(
            data={
                'stocks': data_list,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            },
            message=f"获取同花顺股票数据成功，共 {len(data_list)} 条记录 (总数: {total_count})"
        )
        
    except Exception as e:
        logger.error(f"获取同花顺股票数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票数据失败"
        )


@router.post("/tonghuashun/raw-data", response_model=BaseResponse, summary="接收同花顺原始数据")
async def receive_tonghuashun_raw_data(
    request_data: dict,
    db: AsyncSession = Depends(get_db_session)
):
    """
    接收同花顺原始数据
    支持新旧两种数据格式
    """
    try:
        logger.info(f"🔄 接收到同花顺数据: 类型={type(request_data)}, 大小={len(str(request_data))} 字符")
        logger.info(f"📊 请求数据结构: {list(request_data.keys())}")
        
        # 获取数据源标识
        source = request_data.get('source', 'unknown')
        logger.info(f"📍 数据源: {source}")
        
        # 记录原始日志
        try:
            raw_log_repo = TonghuashunRawLogRepository(db)
            data_list_temp = request_data.get('data', [])
            first_item = data_list_temp[0] if data_list_temp else {}
            
            await raw_log_repo.create_log({
                'source': source,
                'url': first_item.get('url'),
                'request_id': first_item.get('requestId'),
                'request_timestamp': first_item.get('timestamp'),
                'payload_type': 'json',
                'market': 'hs',
                'stock_count': len(data_list_temp),
                'payload': request_data,
                'parse_status': 'pending'
            })
            await db.commit() # 提交原始日志，防止后续处理失败导致日志丢失
        except Exception as log_error:
            logger.error(f"记录原始日志失败: {log_error}")
            # 不阻断后续流程
        
        # 处理数据
        data_list = request_data.get('data', [])
        if not data_list:
            logger.warning("⚠️ 未找到数据字段或数据为空")
            return BaseResponse(
                data={'processed': False, 'total_count': 0, 'processed_count': 0, 'source': source},
                message="未找到有效数据"
            )
        
        total_count = len(data_list)
        processed_count = 0
        successful_stocks = 0
        
        logger.info(f"🚀 开始处理 {total_count} 条数据批次")
        
        for i, item in enumerate(data_list):
            try:
                logger.info(f"📦 处理第 {i+1}/{total_count} 条数据批次")
                logger.info(f"📋 当前批次数据结构: {list(item.keys()) if isinstance(item, dict) else type(item)}")
                
                # 检查是否为multimarketreal数据
                jsonp_data = None
                logger.info(f"🔍 检查数据结构: {item.keys() if isinstance(item, dict) else 'not dict'}")
                
                if 'hs' in item:
                    logger.info("✅ 检测到multimarketreal格式数据（直接hs字段）")
                    # 新格式：直接处理hs字段
                    jsonp_data = item['hs']
                elif 'response' in item:
                    logger.info(f"🔍 发现response字段，检查内容: {type(item['response'])}")
                    if isinstance(item['response'], dict):
                        logger.info(f"🔍 response字段内容: {list(item['response'].keys())}")
                        if 'hs' in item['response']:
                            logger.info("✅ 检测到multimarketreal格式数据（嵌套response.hs字段）")
                            # 嵌套格式：处理response.hs字段
                            jsonp_data = item['response']['hs']
                        else:
                            logger.warning(f"⚠️ response字段中没有hs字段，可用字段: {list(item['response'].keys())}")
                    else:
                        logger.warning(f"⚠️ response字段不是字典类型: {type(item['response'])}")
                else:
                    logger.warning(f"⚠️ 没有找到hs或response字段，可用字段: {list(item.keys()) if isinstance(item, dict) else 'not dict'}")
                
                if jsonp_data is not None:
                    stock_count = len(jsonp_data)
                    logger.info(f"📈 提取到股票数据，包含 {stock_count} 只股票")
                    logger.info(f"🔍 jsonp_data 类型: {type(jsonp_data)}")
                    
                    # 检查数据格式并打印前几只股票的数据结构
                    if isinstance(jsonp_data, list):
                        logger.info("📋 数据格式为列表，每个元素是股票数据数组")
                        for j, stock_data in enumerate(jsonp_data[:3]):
                            if isinstance(stock_data, list) and len(stock_data) > 0:
                                stock_code = stock_data[0] if len(stock_data) > 0 else "未知"
                                logger.info(f"🏷️ 股票样本 {j+1}: {stock_code} = {stock_data}")
                            else:
                                logger.warning(f"⚠️ 股票数据格式异常 {j+1}: {stock_data}")
                    elif isinstance(jsonp_data, dict):
                        logger.info("📋 数据格式为字典，键为股票代码")
                        for j, (stock_code, stock_data) in enumerate(list(jsonp_data.items())[:3]):
                            logger.info(f"🏷️ 股票样本 {j+1}: {stock_code} = {stock_data}")
                    else:
                        logger.error(f"❌ 未知的数据格式: {type(jsonp_data)}")
                    
                    if stock_count > 3:
                        logger.info(f"📊 ... 还有 {stock_count - 3} 只股票")
                    
                    # 提取时间戳参数
                    request_timestamp = item.get('urlTimestamp') or item.get('timestamp')
                    logger.info(f"🕒 提取到请求时间戳: {request_timestamp}")
                    
                    # 使用StockService处理数据
                    logger.info("🔧 开始调用StockService处理数据...")
                    stock_service = StockService(db)
                    result = await stock_service.process_tonghuashun_raw_data(jsonp_data, request_timestamp)
                    logger.info(f"📊 股票数据处理结果: {result}")
                    
                    if result.get('success'):
                        processed_stocks = result.get('processed_count', 0)
                        successful_stocks += processed_stocks
                        logger.info(f"✅ 成功处理 {processed_stocks} 只股票数据")
                    else:
                        errors = result.get('errors', [])
                        logger.error(f"❌ 处理股票数据失败: {errors}")
                        # 打印详细错误信息
                        for error in errors:
                            logger.error(f"🔍 详细错误: {error}")
                else:
                    logger.warning(f"⚠️ 未识别的数据格式，跳过处理: {list(item.keys()) if isinstance(item, dict) else type(item)}")
                
                processed_count += 1
                
            except Exception as item_error:
                logger.error(f"💥 处理单条数据失败: {item_error}")
                logger.error(f"🔍 失败的数据内容: {item}")
                import traceback
                logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
                continue
        
        logger.info(f"🎯 同花顺数据处理完成 - 总批次: {total_count}, 处理成功批次: {processed_count}, 成功处理股票: {successful_stocks}")
        
        return BaseResponse(
            data={
                'processed': True,
                'total_count': total_count,
                'processed_count': processed_count,
                'successful_stocks': successful_stocks,
                'source': source
            },
            message=f"同花顺数据接收成功，共处理 {processed_count}/{total_count} 条数据，成功处理 {successful_stocks} 只股票"
        )
        
    except Exception as e:
        logger.error(f"💥 接收同花顺数据失败: {e}")
        logger.error(f"🔍 请求数据: {request_data}")
        import traceback
        logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理数据失败: {str(e)}"
        )