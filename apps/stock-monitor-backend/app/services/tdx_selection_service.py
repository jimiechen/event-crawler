#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信选股结果服务
负责将TDX选股结果同步到数据库，并区分问财来源
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, delete
from sqlalchemy.dialects.mysql import insert
from loguru import logger

from app.models.tdx_selection import TdxSelectionResult, TdxSelectionBatch
from app.database import db_manager


class TdxSelectionService:
    """通达信选股结果服务"""
    
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
    
    async def create_batch(self, 
                          trade_date: date,
                          sector_code: str,
                          sector_name: str = "") -> str:
        """
        创建选股批次
        
        Args:
            trade_date: 交易日期
            sector_code: 板块代码
            sector_name: 板块名称
            
        Returns:
            str: 批次ID
        """
        batch_id = f"TDX_{trade_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        batch = TdxSelectionBatch(
            batch_id=batch_id,
            trade_date=trade_date,
            sector_code=sector_code,
            sector_name=sector_name or f"三倍量涨停{trade_date.strftime('%m%d')}",
            strategy_name="3x_volume_limit_up",
            status="running",
            data_sync_status="pending",
            selection_status="pending",
            screenshot_status="pending",
            feishu_sync_status="pending",
            started_at=datetime.now(),
            source="tdx"
        )
        
        self.db_session.add(batch)
        await self.db_session.commit()
        
        logger.info(f"创建TDX选股批次: {batch_id}, 板块: {sector_code}")
        return batch_id
    
    async def update_batch_status(self,
                                  batch_id: str,
                                  status: Optional[str] = None,
                                  data_sync_status: Optional[str] = None,
                                  selection_status: Optional[str] = None,
                                  screenshot_status: Optional[str] = None,
                                  feishu_sync_status: Optional[str] = None,
                                  total_stocks: Optional[int] = None,
                                  error_message: Optional[str] = None):
        """更新批次状态"""
        result = await self.db_session.execute(
            select(TdxSelectionBatch).where(TdxSelectionBatch.batch_id == batch_id)
        )
        batch = result.scalar_one_or_none()
        
        if not batch:
            logger.warning(f"批次不存在: {batch_id}")
            return
        
        if status:
            batch.status = status
        if data_sync_status:
            batch.data_sync_status = data_sync_status
        if selection_status:
            batch.selection_status = selection_status
        if screenshot_status:
            batch.screenshot_status = screenshot_status
        if feishu_sync_status:
            batch.feishu_sync_status = feishu_sync_status
        if total_stocks is not None:
            batch.total_stocks = total_stocks
        if error_message:
            batch.error_message = error_message
        
        # 如果完成，记录完成时间
        if status in ["completed", "failed"]:
            batch.completed_at = datetime.now()
            if batch.started_at:
                batch.duration = Decimal(str((batch.completed_at - batch.started_at).total_seconds()))
        
        await self.db_session.commit()
        logger.info(f"更新批次状态: {batch_id}, status={status}")
    
    async def save_selection_results(self,
                                     batch_id: str,
                                     trade_date: date,
                                     sector_code: str,
                                     selected_stocks: List[Dict[str, Any]]) -> int:
        """
        保存选股结果到数据库
        
        Args:
            batch_id: 批次ID
            trade_date: 交易日期
            sector_code: 板块代码
            selected_stocks: 选中的股票列表，每个股票包含详细信息
            
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
                
                # 检查是否已存在
                result = await self.db_session.execute(
                    select(TdxSelectionResult).where(
                        and_(
                            TdxSelectionResult.stock_code == stock_code,
                            TdxSelectionResult.trade_date == trade_date
                        )
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 更新现有记录
                    existing.sector_code = sector_code
                    existing.batch_id = batch_id
                    existing.stock_name = stock_data.get("stock_name", existing.stock_name)
                    existing.open_price = self._to_decimal(stock_data.get("open_price"))
                    existing.close_price = self._to_decimal(stock_data.get("close_price"))
                    existing.high_price = self._to_decimal(stock_data.get("high_price"))
                    existing.low_price = self._to_decimal(stock_data.get("low_price"))
                    existing.prev_close = self._to_decimal(stock_data.get("prev_close"))
                    existing.volume = stock_data.get("volume")
                    existing.prev_volume = stock_data.get("prev_volume")
                    existing.volume_ratio = self._to_decimal(stock_data.get("volume_ratio"))
                    existing.amount = self._to_decimal(stock_data.get("amount"))
                    existing.change_percent = self._to_decimal(stock_data.get("change_percent"))
                    existing.limit_up_price = self._to_decimal(stock_data.get("limit_up_price"))
                    existing.is_limit_up = stock_data.get("is_limit_up", True)
                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    result = TdxSelectionResult(
                        stock_code=stock_code,
                        stock_name=stock_data.get("stock_name"),
                        trade_date=trade_date,
                        sector_code=sector_code,
                        sector_name=stock_data.get("sector_name", ""),
                        open_price=self._to_decimal(stock_data.get("open_price")),
                        close_price=self._to_decimal(stock_data.get("close_price")),
                        high_price=self._to_decimal(stock_data.get("high_price")),
                        low_price=self._to_decimal(stock_data.get("low_price")),
                        prev_close=self._to_decimal(stock_data.get("prev_close")),
                        volume=stock_data.get("volume"),
                        prev_volume=stock_data.get("prev_volume"),
                        volume_ratio=self._to_decimal(stock_data.get("volume_ratio")),
                        amount=self._to_decimal(stock_data.get("amount")),
                        change_percent=self._to_decimal(stock_data.get("change_percent")),
                        limit_up_price=self._to_decimal(stock_data.get("limit_up_price")),
                        is_limit_up=stock_data.get("is_limit_up", True),
                        strategy_name="3x_volume_limit_up",
                        source="tdx",  # 标记为TDX来源
                        screenshot_path=stock_data.get("screenshot_path"),
                        extra_data=stock_data.get("extra_data"),
                        remark=stock_data.get("remark")
                    )
                    self.db_session.add(result)
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"保存选股结果失败: {stock_data.get('stock_code')}, 错误: {e}")
                continue
        
        await self.db_session.commit()
        logger.info(f"保存选股结果完成: {saved_count} 条记录")
        return saved_count
    
    async def get_selection_results(self,
                                    trade_date: Optional[date] = None,
                                    sector_code: Optional[str] = None,
                                    source: str = "tdx") -> List[TdxSelectionResult]:
        """
        获取选股结果
        
        Args:
            trade_date: 交易日期
            sector_code: 板块代码
            source: 数据来源 (tdx/wencai)
            
        Returns:
            List[TdxSelectionResult]: 选股结果列表
        """
        query = select(TdxSelectionResult)
        
        if trade_date:
            query = query.where(TdxSelectionResult.trade_date == trade_date)
        if sector_code:
            query = query.where(TdxSelectionResult.sector_code == sector_code)
        if source:
            query = query.where(TdxSelectionResult.source == source)
        
        query = query.order_by(TdxSelectionResult.change_percent.desc())
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def update_feishu_sync_status(self,
                                        stock_code: str,
                                        trade_date: date,
                                        feishu_record_id: str):
        """更新飞书同步状态"""
        result = await self.db_session.execute(
            select(TdxSelectionResult).where(
                and_(
                    TdxSelectionResult.stock_code == stock_code,
                    TdxSelectionResult.trade_date == trade_date
                )
            )
        )
        record = result.scalar_one_or_none()
        
        if record:
            record.feishu_synced = True
            record.feishu_sync_time = datetime.now()
            record.feishu_record_id = feishu_record_id
            await self.db_session.commit()
            logger.info(f"更新飞书同步状态: {stock_code}, record_id={feishu_record_id}")
    
    async def get_latest_selection_by_date(self, trade_date: date) -> Optional[TdxSelectionBatch]:
        """获取指定日期的最新选股批次"""
        result = await self.db_session.execute(
            select(TdxSelectionBatch)
            .where(TdxSelectionBatch.trade_date == trade_date)
            .order_by(TdxSelectionBatch.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """转换为Decimal类型"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    async def get_distinct_sources_count(self, trade_date: date) -> Dict[str, int]:
        """
        获取不同来源的选股数量统计
        
        Args:
            trade_date: 交易日期
            
        Returns:
            Dict[str, int]: 各来源的数量
        """
        from sqlalchemy import func
        
        result = await self.db_session.execute(
            select(
                TdxSelectionResult.source,
                func.count(TdxSelectionResult.id).label("count")
            )
            .where(TdxSelectionResult.trade_date == trade_date)
            .group_by(TdxSelectionResult.source)
        )
        
        return {row.source: row.count for row in result.all()}
