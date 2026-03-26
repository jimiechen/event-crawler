#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日复盘服务
复盘时更新股票池的日K线数据
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Set
from sqlalchemy import select, and_
from loguru import logger

from app.database import db_manager
from app.models.stock import WencaiStock, WencaiCrawlBatch
from app.services.tdx_daily_data_service import TdxDailyDataService


class DailyReviewService:
    """每日复盘服务"""
    
    def __init__(self, tdx_client=None):
        """
        初始化
        
        Args:
            tdx_client: 通达信客户端实例
        """
        self.tdx_client = tdx_client
        self.daily_service = TdxDailyDataService(tdx_client)
    
    async def update_stock_pool_daily_data(
        self,
        trade_date: date,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        复盘时更新股票池的日线数据
        
        逻辑:
        1. 获取最近N天内所有选股批次
        2. 获取这些批次包含的所有股票
        3. 同步这些股票到trade_date的日线数据
        
        Args:
            trade_date: 复盘日期
            lookback_days: 回溯天数，默认30天
            
        Returns:
            Dict: 更新结果统计
        """
        logger.info(f"开始复盘数据更新: {trade_date}, 回溯 {lookback_days} 天")
        
        try:
            # 1. 获取最近N天的选股批次
            start_date = trade_date - timedelta(days=lookback_days)
            batches = await self._get_recent_batches(start_date, trade_date)
            
            if not batches:
                logger.info(f"最近 {lookback_days} 天内无选股批次")
                return {
                    "status": "success",
                    "trade_date": trade_date,
                    "batches_count": 0,
                    "stocks_count": 0,
                    "synced_count": 0
                }
            
            logger.info(f"找到 {len(batches)} 个选股批次")
            
            # 2. 获取所有股票代码（去重）
            all_stocks: Set[str] = set()
            for batch in batches:
                stocks = await self._get_stocks_by_batch(batch.id)
                all_stocks.update(stocks)
            
            if not all_stocks:
                logger.info("无股票需要更新")
                return {
                    "status": "success",
                    "trade_date": trade_date,
                    "batches_count": len(batches),
                    "stocks_count": 0,
                    "synced_count": 0
                }
            
            stock_list = list(all_stocks)
            logger.info(f"需要更新 {len(stock_list)} 只股票的日线数据")
            
            # 3. 同步日线数据（只更新当天的数据）
            sync_result = await self.daily_service.sync_daily_data_for_selection(
                stock_codes=stock_list,
                end_date=trade_date,
                batch_id=None,  # 复盘更新不关联特定批次
                days=1  # 只更新当天的数据
            )
            
            # 4. 更新这些股票的量价得分
            logger.info("更新量价得分...")
            from app.services.volume_analysis_service import VolumeAnalysisService
            
            async with db_manager.get_session() as session:
                for stock_code in stock_list:
                    try:
                        code = stock_code.split('.')[0] if '.' in stock_code else stock_code
                        await VolumeAnalysisService.generate_daily_tags(
                            code=code,
                            target_date=trade_date,
                            session=session
                        )
                    except Exception as e:
                        logger.warning(f"更新 {stock_code} 得分失败: {e}")
            
            result = {
                "status": "success",
                "trade_date": trade_date,
                "batches_count": len(batches),
                "stocks_count": len(stock_list),
                "synced_count": sync_result.get("total_synced", 0),
                "failed_count": sync_result.get("failed_count", 0),
                "failed_stocks": sync_result.get("failed_stocks", [])
            }
            
            logger.info(f"复盘数据更新完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"复盘数据更新失败: {e}")
            return {
                "status": "failed",
                "trade_date": trade_date,
                "error": str(e)
            }
    
    async def _get_recent_batches(
        self,
        start_date: date,
        end_date: date
    ) -> List[WencaiCrawlBatch]:
        """
        获取日期范围内的选股批次
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[WencaiCrawlBatch]: 批次列表
        """
        async with db_manager.get_session() as session:
            stmt = select(WencaiCrawlBatch).where(
                and_(
                    WencaiCrawlBatch.source == 'tdx',
                    WencaiCrawlBatch.query_date >= start_date,
                    WencaiCrawlBatch.query_date <= end_date
                )
            ).order_by(WencaiCrawlBatch.query_date.desc())
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def _get_stocks_by_batch(self, batch_id: int) -> List[str]:
        """
        获取批次包含的股票代码
        
        Args:
            batch_id: 批次ID
            
        Returns:
            List[str]: 股票代码列表
        """
        async with db_manager.get_session() as session:
            stmt = select(WencaiStock.stock_code).where(
                WencaiStock.crawl_batch_id == str(batch_id)
            )
            result = await session.execute(stmt)
            return [r[0] for r in result.all()]
    
    async def get_stock_pool_status(
        self,
        trade_date: date,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        获取股票池状态
        
        Args:
            trade_date: 日期
            lookback_days: 回溯天数
            
        Returns:
            Dict: 股票池状态信息
        """
        start_date = trade_date - timedelta(days=lookback_days)
        
        async with db_manager.get_session() as session:
            # 获取批次数量
            batch_stmt = select(WencaiCrawlBatch).where(
                and_(
                    WencaiCrawlBatch.source == 'tdx',
                    WencaiCrawlBatch.query_date >= start_date,
                    WencaiCrawlBatch.query_date <= trade_date
                )
            )
            batch_result = await session.execute(batch_stmt)
            batches = batch_result.scalars().all()
            
            # 获取股票数量
            batch_ids = [str(b.id) for b in batches]
            if batch_ids:
                stock_stmt = select(WencaiStock.stock_code).where(
                    WencaiStock.crawl_batch_id.in_(batch_ids)
                ).distinct()
                stock_result = await session.execute(stock_stmt)
                stocks = [r[0] for r in stock_result.all()]
            else:
                stocks = []
            
            return {
                "trade_date": trade_date,
                "lookback_days": lookback_days,
                "batches_count": len(batches),
                "unique_stocks_count": len(stocks),
                "batch_details": [
                    {
                        "id": b.id,
                        "date": b.query_date.isoformat(),
                        "sector_code": b.sector_code,
                        "total_records": b.total_records
                    }
                    for b in batches
                ]
            }
