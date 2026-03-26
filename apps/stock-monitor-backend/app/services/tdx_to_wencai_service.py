#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信选股结果同步到问财表服务
将TDX选股结果存储到现有的问财表结构中，通过source字段区分来源
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from loguru import logger

from app.models.stock import WencaiStock, WencaiCrawlBatch
from app.database import db_manager


class TdxToWencaiService:
    """
    TDX选股结果同步到问财表服务
    
    字段对齐说明：
    - 问财: volume (手) -> TDX: volume (股) / 100
    - 问财: current_price (元) -> TDX: close_price (元)
    - 问财: turnover (元) -> TDX: amount (千元) * 1000
    """
    
    def __init__(self):
        self.db_session = None
    
    async def __aenter__(self):
        await db_manager.initialize()
        if db_manager.session_factory is None:
            raise RuntimeError("数据库会话工厂未初始化")
        self.db_session = db_manager.session_factory()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db_session:
            await self.db_session.close()
    
    async def create_tdx_batch(self,
                               trade_date: date,
                               sector_code: str,
                               sector_name: str = "") -> int:
        """
        创建TDX选股批次（使用问财批次表）
        
        Args:
            trade_date: 交易日期
            sector_code: 板块代码
            sector_name: 板块名称
            
        Returns:
            int: 批次ID
        """
        # 板块命名格式: 3倍量涨停260201 (年份后两位+月份+日期)
        sector_name = sector_name or f"3倍量涨停{trade_date.strftime('%y%m%d')}"
        # 板块代码格式: 3BL260201
        sector_code = sector_code or f"3BL{trade_date.strftime('%y%m%d')}"
        batch_name = f"TDX_{trade_date.strftime('%Y%m%d')}_{sector_code}"
        
        batch = WencaiCrawlBatch(
            batch_name=batch_name,
            query_condition=f"通达信三倍量+涨停选股 {sector_code}",
            status="running",
            started_at=datetime.now(),
            total_records=0,
            success_records=0,
            failed_records=0,
            source="tdx",  # 标记为TDX来源
            sector_code=sector_code,
            query_date=trade_date
        )
        
        self.db_session.add(batch)
        await self.db_session.commit()
        await self.db_session.refresh(batch)
        
        logger.info(f"创建TDX批次: {batch.id}, 名称: {batch_name}, 板块: {sector_code} ({sector_name})")
        return batch.id
    
    async def update_batch_status(self,
                                  batch_id: int,
                                  status: str,
                                  total_records: int = None,
                                  success_records: int = None,
                                  error_message: str = None):
        """更新批次状态"""
        result = await self.db_session.execute(
            select(WencaiCrawlBatch).where(WencaiCrawlBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        
        if batch:
            batch.status = status
            if total_records is not None:
                batch.total_records = total_records
            if success_records is not None:
                batch.success_records = success_records
            if error_message:
                batch.error_message = error_message
            if status in ["completed", "failed"]:
                batch.completed_at = datetime.now()
            
            await self.db_session.commit()
            logger.info(f"更新批次状态: {batch_id}, status={status}")
    
    async def save_tdx_selection_results(self,
                                         batch_id: int,
                                         trade_date: date,
                                         selected_stocks: List[Dict[str, Any]]) -> int:
        """
        保存TDX选股结果到问财股票表
        
        Args:
            batch_id: 批次ID
            trade_date: 交易日期
            selected_stocks: 选中的股票列表
            
        Returns:
            int: 保存的记录数
        """
        if not selected_stocks:
            logger.info("没有选股结果需要保存")
            return 0
        
        saved_count = 0
        
        for stock_data in selected_stocks:
            try:
                stock_code = stock_data.get("stock_code")
                if not stock_code:
                    continue
                
                # 检查是否已存在（同一天同一股票）
                result = await self.db_session.execute(
                    select(WencaiStock).where(
                        and_(
                            WencaiStock.stock_code == stock_code,
                            WencaiStock.crawl_batch_id == str(batch_id)
                        )
                    )
                )
                existing = result.scalar_one_or_none()
                
                # 字段单位转换
                # TDX: volume是股数，问财: volume是手数 -> 除以100
                volume = stock_data.get("volume")
                if volume:
                    volume = int(volume / 100)  # 股 -> 手
                
                # TDX: amount是千元，问财: turnover是元 -> 乘以1000
                turnover = stock_data.get("amount")
                if turnover:
                    turnover = Decimal(str(turnover)) * 1000  # 千元 -> 元
                
                if existing:
                    # 更新现有记录
                    existing.stock_name = stock_data.get("stock_name", existing.stock_name)
                    existing.current_price = self._to_decimal(stock_data.get("close_price"))
                    existing.volume = volume
                    existing.turnover = turnover
                    existing.change_percent = self._to_decimal(stock_data.get("change_percent"))
                    existing.volume_ratio = self._to_decimal(stock_data.get("volume_ratio"))
                    existing.open_price = self._to_decimal(stock_data.get("open_price"))
                    existing.high_price = self._to_decimal(stock_data.get("high_price"))
                    existing.low_price = self._to_decimal(stock_data.get("low_price"))
                    existing.prev_close = self._to_decimal(stock_data.get("prev_close"))
                    existing.is_limit_up = stock_data.get("is_limit_up", True)
                    existing.strategy_name = stock_data.get("strategy_name", "3x_volume_limit_up")
                    existing.source = "tdx"
                    existing.is_active = True
                else:
                    # 创建新记录
                    wencai_stock = WencaiStock(
                        crawl_batch_id=str(batch_id),
                        stock_code=stock_code,
                        stock_name=stock_data.get("stock_name", ""),
                        current_price=self._to_decimal(stock_data.get("close_price")),
                        volume=volume,
                        turnover=turnover,
                        change_percent=self._to_decimal(stock_data.get("change_percent")),
                        volume_ratio=self._to_decimal(stock_data.get("volume_ratio")),
                        open_price=self._to_decimal(stock_data.get("open_price")),
                        high_price=self._to_decimal(stock_data.get("high_price")),
                        low_price=self._to_decimal(stock_data.get("low_price")),
                        prev_close=self._to_decimal(stock_data.get("prev_close")),
                        is_limit_up=stock_data.get("is_limit_up", True),
                        strategy_name=stock_data.get("strategy_name", "3x_volume_limit_up"),
                        source="tdx",  # 标记为TDX来源
                        is_active=True
                    )
                    self.db_session.add(wencai_stock)
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"保存选股结果失败: {stock_data.get('stock_code')}, 错误: {e}")
                continue
        
        await self.db_session.commit()
        
        # 更新批次统计
        await self.update_batch_status(
            batch_id=batch_id,
            status="completed",
            total_records=saved_count,
            success_records=saved_count
        )
        
        logger.info(f"保存TDX选股结果完成: {saved_count} 条记录")
        return saved_count
    
    async def get_tdx_selection_results(self,
                                        trade_date: Optional[date] = None,
                                        sector_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取TDX选股结果
        
        Args:
            trade_date: 交易日期
            sector_code: 板块代码
            
        Returns:
            List[Dict]: 选股结果列表
        """
        # 先查询批次
        batch_query = select(WencaiCrawlBatch).where(WencaiCrawlBatch.source == "tdx")
        
        if trade_date:
            batch_query = batch_query.where(WencaiCrawlBatch.query_date == trade_date)
        if sector_code:
            batch_query = batch_query.where(WencaiCrawlBatch.sector_code == sector_code)
        
        batch_query = batch_query.order_by(WencaiCrawlBatch.created_at.desc())
        
        result = await self.db_session.execute(batch_query)
        batches = result.scalars().all()
        
        if not batches:
            return []
        
        # 获取这些批次的股票
        batch_ids = [str(b.id) for b in batches]
        
        stock_query = select(WencaiStock).where(
            and_(
                WencaiStock.crawl_batch_id.in_(batch_ids),
                WencaiStock.source == "tdx"
            )
        ).order_by(WencaiStock.change_percent.desc())
        
        result = await self.db_session.execute(stock_query)
        stocks = result.scalars().all()
        
        return [
            {
                "stock_code": s.stock_code,
                "stock_name": s.stock_name,
                "current_price": float(s.current_price) if s.current_price else None,
                "volume": s.volume,
                "turnover": float(s.turnover) if s.turnover else None,
                "change_percent": float(s.change_percent) if s.change_percent else None,
                "volume_ratio": float(s.volume_ratio) if s.volume_ratio else None,
                "is_limit_up": s.is_limit_up,
                "source": s.source,
                "batch_id": s.crawl_batch_id
            }
            for s in stocks
        ]
    
    async def get_distinct_sources_count(self, trade_date: date) -> Dict[str, int]:
        """
        获取不同来源的选股数量统计
        
        Args:
            trade_date: 交易日期
            
        Returns:
            Dict[str, int]: 各来源的数量
        """
        from sqlalchemy import func
        
        # 获取该日期的所有批次
        result = await self.db_session.execute(
            select(WencaiCrawlBatch.id).where(WencaiCrawlBatch.query_date == trade_date)
        )
        batch_ids = [str(row[0]) for row in result.all()]
        
        if not batch_ids:
            return {}
        
        # 统计各来源数量
        result = await self.db_session.execute(
            select(
                WencaiStock.source,
                func.count(WencaiStock.id).label("count")
            )
            .where(WencaiStock.crawl_batch_id.in_(batch_ids))
            .group_by(WencaiStock.source)
        )
        
        return {row.source: row.count for row in result.all()}
    
    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """转换为Decimal类型"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None


# 便捷函数
async def sync_tdx_selection_to_wencai(
    trade_date: date,
    sector_code: str,
    selected_stocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    同步TDX选股结果到问财表
    
    Args:
        trade_date: 交易日期
        sector_code: 板块代码
        selected_stocks: 选中的股票列表
        
    Returns:
        Dict: 同步结果
    """
    async with TdxToWencaiService() as service:
        # 创建批次
        batch_id = await service.create_tdx_batch(
            trade_date=trade_date,
            sector_code=sector_code
        )
        
        # 保存选股结果
        saved_count = await service.save_tdx_selection_results(
            batch_id=batch_id,
            trade_date=trade_date,
            selected_stocks=selected_stocks
        )
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "saved_count": saved_count
        }
