#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票日线数据仓库
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from sqlalchemy import select, func, desc, delete, and_
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.models.stock_daily import StockDaily, StockScoreResult, TaskLog
from app.models.stock import MonitorList, WencaiStock, StockInfo
from app.database import DatabaseManager

class StockDailyRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def batch_save_daily_data_ignore(self, data_list: List[Dict[str, Any]]) -> int:
        """批量保存日线数据(存在则忽略)"""
        if not data_list:
            return 0

        async with self.db_manager.get_session() as session:
            # MySQL: INSERT IGNORE
            stmt = mysql_insert(StockDaily).values(data_list)
            insert_ignore_stmt = stmt.prefix_with('IGNORE')
            
            try:
                result = await session.execute(insert_ignore_stmt)
                await session.commit()
                return result.rowcount
            except Exception as e:
                # SQLite fallback or other error
                await session.rollback()
                
                count = 0
                for item in data_list:
                    existing = await session.execute(
                        select(StockDaily).where(
                            StockDaily.code == item['code'],
                            StockDaily.trade_date == item['trade_date']
                        )
                    )
                    obj = existing.scalar_one_or_none()
                    
                    if not obj:
                        new_obj = StockDaily(**item)
                        session.add(new_obj)
                        count += 1
                
                await session.commit()
                return count

    async def batch_save_daily_data(self, data_list: List[Dict[str, Any]]) -> int:
        """批量保存日线数据(存在则更新)"""
        if not data_list:
            return 0

        async with self.db_manager.get_session() as session:
            # 使用MySQL的ON DUPLICATE KEY UPDATE
            # 或者先查询后更新/插入
            # 这里为了通用性(支持SQLite)，可能需要逐条处理或分批处理
            # 但为了性能，优先尝试 bulk upsert
            
            # 由于SQLAlchemy的ORM bulk operations在不同数据库下表现不同
            # 且SQLite不支持ON DUPLICATE KEY UPDATE
            # 我们这里使用简单的策略：先尝试插入，如果冲突则忽略(或者更新)
            # 考虑到是日线数据，通常是插入新的。如果是更新，可能是修正数据。
            
            # 对于SQLite，可以使用 insert().on_conflict_do_update() (SQLAlchemy 1.4+)
            # 这里假设使用 SQLite 或 MySQL
            
            stmt = mysql_insert(StockDaily).values(data_list)
            
            # 构建更新字段字典
            update_dict = {
                col.name: col for col in stmt.inserted 
                if col.name not in ['id', 'created_at', 'code', 'trade_date']
            }
            
            # MySQL语法
            on_duplicate_key_stmt = stmt.on_duplicate_key_update(**update_dict)
            
            try:
                await session.execute(on_duplicate_key_stmt)
                await session.commit()
                return len(data_list)
            except Exception as e:
                # 如果是SQLite，上面的语句会失败
                # 回退到逐条处理或使用SQLite特定语法
                # 这里为了简单，如果失败且是SQLite，使用merge
                await session.rollback()
                
                count = 0
                for item in data_list:
                    # 查找是否存在
                    existing = await session.execute(
                        select(StockDaily).where(
                            StockDaily.code == item['code'],
                            StockDaily.trade_date == item['trade_date']
                        )
                    )
                    obj = existing.scalar_one_or_none()
                    
                    if obj:
                        for k, v in item.items():
                            setattr(obj, k, v)
                    else:
                        new_obj = StockDaily(**item)
                        session.add(new_obj)
                    count += 1
                
                await session.commit()
                return count

    async def save_stock_scores(self, score_results: List[Dict[str, Any]]) -> int:
        """批量保存股票评分结果"""
        if not score_results:
            return 0

        async with self.db_manager.get_session() as session:
            # 构建插入语句
            # StockScoreResult 定义在 app.models.stock_daily
            # 假设 StockScoreResult 有 code, trade_date 联合唯一索引
            stmt = mysql_insert(StockScoreResult).values(score_results)
            
            # 构建更新字段
            update_dict = {
                col.name: col for col in stmt.inserted 
                if col.name not in ['id', 'created_at', 'code', 'trade_date']
            }
            
            on_duplicate_key_stmt = stmt.on_duplicate_key_update(**update_dict)
            
            try:
                await session.execute(on_duplicate_key_stmt)
                await session.commit()
                return len(score_results)
            except Exception as e:
                await session.rollback()
                # 简单回退策略：先删后插 (针对同一天同一股票)
                # 或者逐个处理
                # 这里为了简单，针对SQLite环境或异常情况，我们先尝试删除这批(code, date)的数据，再插入
                # 注意：这可能会有性能影响
                # 更好的方式是逐个 merge
                
                count = 0
                for item in score_results:
                    # 检查是否存在
                    existing = await session.execute(
                        select(StockScoreResult).where(
                            StockScoreResult.code == item['code'],
                            StockScoreResult.trade_date == item['trade_date']
                        )
                    )
                    obj = existing.scalar_one_or_none()
                    
                    if obj:
                        for k, v in item.items():
                            setattr(obj, k, v)
                    else:
                        new_obj = StockScoreResult(**item)
                        session.add(new_obj)
                    count += 1
                
                await session.commit()
                return count

    async def get_latest_date(self, code: str) -> Optional[date]:
        """获取某股票最近的交易日期"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(func.max(StockDaily.trade_date)).where(StockDaily.code == code)
            )
            return result.scalar()

    async def get_latest_adj_factor(self, code: str) -> Optional[float]:
        """获取某股票最新的复权因子"""
        async with self.db_manager.get_session() as session:
            stmt = select(StockDaily.adj_factor).where(
                StockDaily.code == code,
                StockDaily.adj_factor.is_not(None)
            ).order_by(StockDaily.trade_date.desc()).limit(1)
            result = await session.execute(stmt)
            return result.scalar()


    async def get_target_stocks(self) -> List[str]:
        """获取需要采集的股票代码列表(从StockInfo获取)"""
        async with self.db_manager.get_session() as session:
            # 从StockInfo表获取所有股票代码
            result = await session.execute(select(StockInfo.code).distinct())
            return [r[0] for r in result.all()]

    async def sync_stock_pool(self) -> Dict[str, int]:
        """同步股票池数据(自选股/问财)到StockInfo表"""
        # 注意：由于StockPool已废弃，此方法逻辑可能需要更新或废弃
        # 原逻辑是同步 MonitorList 和 WencaiStock 到 StockPool
        # 现逻辑应为同步 MonitorList 和 WencaiStock 到 StockInfo
        
        async with self.db_manager.get_session() as session:
            # 1. 获取最新数据
            # 自选股
            monitor_result = await session.execute(
                select(MonitorList.code, StockInfo.name)
                .join(StockInfo, MonitorList.code == StockInfo.code, isouter=True)
                .where(MonitorList.is_active == True)
            )
            monitor_list = monitor_result.all()
            
            # 问财股
            wencai_result = await session.execute(select(WencaiStock.stock_code, WencaiStock.stock_name))
            wencai_list = wencai_result.all()
            
            count_monitor = 0
            count_wencai = 0
            
            # 2. 更新 StockInfo 的 source 字段
            # 优先处理 MonitorList (self_selected)
            for code, name in monitor_list:
                stmt = select(StockInfo).where(StockInfo.code == code)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                
                if existing:
                    existing.source = 'self_selected'
                    existing.is_active = True
                else:
                    # 如果不存在，创建新的 (虽然理论上MonitorList有外键约束，但为了健壮性)
                    new_stock = StockInfo(
                        code=code,
                        name=name or code, # Fallback name
                        source='self_selected',
                        is_active=True
                    )
                    session.add(new_stock)
                count_monitor += 1
                
            # 处理 WencaiStock (wencai)
            # 如果已经是 self_selected，则保持 self_selected (或变为 both? 目前只存单个 source)
            # 假设 self_selected 优先级更高
            for code, name in wencai_list:
                stmt = select(StockInfo).where(StockInfo.code == code)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                
                if existing:
                    if existing.source != 'self_selected':
                        existing.source = 'wencai'
                        # existing.is_active = True # 问财同步过来的通常默认活跃? 用户之前要求 is_active=0
                        # 根据用户最新要求：is_active=0
                        # 但如果是 self_selected 变为 wencai (不可能，上面已过滤)，或者纯新 wencai
                        # 这里我们只更新 source
                else:
                     # 理论上应该在问财同步时就插入了 StockInfo
                     # 这里做个兜底
                    new_stock = StockInfo(
                        code=code,
                        name=name,
                        source='wencai',
                        is_active=False
                    )
                    session.add(new_stock)
                count_wencai += 1
            
            await session.commit()
            
            return {
                "self_selected": count_monitor,
                "wencai": count_wencai,
                "total_records": count_monitor + count_wencai # Approximate
            }

    async def get_stock_pool_map(self) -> Dict[str, str]:
        """获取股票代码对应的池类型映射"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(StockInfo.code, StockInfo.source))
            data = result.all()
            
            pool_map = {}
            for code, source in data:
                if source:
                    pool_map[code] = source
                        
            return pool_map


    async def save_task_log(self, log_data: Dict[str, Any]) -> TaskLog:
        """保存任务日志"""
        async with self.db_manager.get_session() as session:
            log = TaskLog(**log_data)
            session.add(log)
            await session.commit()
            return log

    async def get_daily_data(self, code: str, start_date: date, end_date: date) -> List[StockDaily]:
        """获取指定范围的日线数据"""
        async with self.db_manager.get_session() as session:
            stmt = select(StockDaily).where(
                StockDaily.code == code,
                StockDaily.trade_date >= start_date,
                StockDaily.trade_date <= end_date
            ).order_by(StockDaily.trade_date.asc())
            result = await session.execute(stmt)
            return result.scalars().all()

    async def query_daily_data(
        self, 
        page: int, 
        page_size: int,
        code: Optional[str] = None, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Tuple[List[StockDaily], int]:
        """
        分页查询日线数据
        """
        async with self.db_manager.get_session() as session:
            stmt = select(StockDaily)
            count_stmt = select(func.count(StockDaily.id))
            
            conditions = []
            if code:
                conditions.append(StockDaily.code.like(f"%{code}%"))
            if start_date:
                conditions.append(StockDaily.trade_date >= start_date)
            if end_date:
                conditions.append(StockDaily.trade_date <= end_date)
            if min_price is not None:
                conditions.append(StockDaily.close >= min_price)
            if max_price is not None:
                conditions.append(StockDaily.close <= max_price)
                
            if conditions:
                stmt = stmt.where(*conditions)
                count_stmt = count_stmt.where(*conditions)
                
            # 获取总数
            total_result = await session.execute(count_stmt)
            total = total_result.scalar()
            
            # 获取分页数据
            stmt = stmt.order_by(StockDaily.trade_date.desc(), StockDaily.code.asc())
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
            
            result = await session.execute(stmt)
            return result.scalars().all(), total

