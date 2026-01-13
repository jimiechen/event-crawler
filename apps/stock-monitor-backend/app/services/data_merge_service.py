#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据合并服务
支持CSV、Tushare、akshare数据源的合并和去重
"""

import os
import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.mysql import insert

from app.models.stock_daily import StockDaily
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class DataMergeService:
    """数据合并服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def merge_csv_to_database(
        self,
        csv_file_path: str,
        date_column: str = "trade_date",
        code_column: str = "code",
        keep_latest: bool = True,
        update_csv: bool = True
    ) -> Dict[str, Any]:
        """
        合并CSV文件到数据库
        
        Args:
            csv_file_path: CSV文件路径
            date_column: 日期列名
            code_column: 股票代码列名
            keep_latest: 是否保留最新数据（按日期）
            update_csv: 是否更新CSV文件
            
        Returns:
            合并结果统计
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV文件不存在: {csv_file_path}")

        # 读取CSV文件
        csv_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_data.append(row)

        logger.info(f"从CSV文件读取到 {len(csv_data)} 条记录")

        # 合并到数据库
        result = await self.merge_data_to_database(
            data=csv_data,
            date_column=date_column,
            code_column=code_column,
            keep_latest=keep_latest
        )

        # 如果需要更新CSV文件
        if update_csv:
            await self.update_csv_from_database(
                csv_file_path=csv_file_path,
                date_column=date_column,
                code_column=code_column
            )

        return result

    async def merge_data_to_database(
        self,
        data: List[Dict[str, Any]],
        date_column: str = "trade_date",
        code_column: str = "code",
        keep_latest: bool = True
    ) -> Dict[str, Any]:
        """
        合并数据到数据库
        
        Args:
            data: 数据列表
            date_column: 日期列名
            code_column: 股票代码列名
            keep_latest: 是否保留最新数据（按日期）
            
        Returns:
            合并结果统计
        """
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for row in data:
            try:
                # 解析日期
                trade_date_str = row.get(date_column)
                if not trade_date_str:
                    logger.warning(f"记录缺少日期字段: {row}")
                    skipped_count += 1
                    continue

                # 尝试解析日期
                if isinstance(trade_date_str, str):
                    if len(trade_date_str) == 8:  # 20240101格式
                        trade_date = datetime.strptime(trade_date_str, "%Y%m%d").date()
                    elif len(trade_date_str) == 10:  # 2024-01-01格式
                        trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d").date()
                    else:
                        logger.warning(f"无法解析日期格式: {trade_date_str}")
                        skipped_count += 1
                        continue
                elif isinstance(trade_date_str, date):
                    trade_date = trade_date_str
                else:
                    logger.warning(f"不支持的日期类型: {type(trade_date_str)}")
                    skipped_count += 1
                    continue

                # 解析股票代码
                stock_code = row.get(code_column)
                if not stock_code:
                    logger.warning(f"记录缺少股票代码字段: {row}")
                    skipped_count += 1
                    continue

                # 检查是否已存在
                stmt = select(StockDaily).where(
                    StockDaily.code == stock_code,
                    StockDaily.trade_date == trade_date
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                # 准备数据
                stock_data = {
                    "code": stock_code,
                    "trade_date": trade_date,
                    "open": self._parse_decimal(row.get("open")),
                    "close": self._parse_decimal(row.get("close")),
                    "high": self._parse_decimal(row.get("high")),
                    "low": self._parse_decimal(row.get("low")),
                    "vol": self._parse_int(row.get("vol")),
                    "amount": self._parse_decimal(row.get("amount")),
                    "turnover_rate": self._parse_decimal(row.get("turnover_rate")),
                    "volume_ratio": self._parse_decimal(row.get("volume_ratio")),
                    "adj_factor": self._parse_decimal(row.get("adj_factor"))
                }

                if existing:
                    # 如果已存在，检查是否需要更新
                    if keep_latest:
                        # 保留最新数据（这里简单处理，实际可能需要更复杂的逻辑）
                        # 比如比较更新时间或其他字段
                        logger.debug(f"记录已存在，跳过: {stock_code} - {trade_date}")
                        skipped_count += 1
                    else:
                        # 更新现有记录
                        for key, value in stock_data.items():
                            if value is not None:
                                setattr(existing, key, value)
                        updated_count += 1
                else:
                    # 插入新记录
                    new_stock = StockDaily(**stock_data)
                    self.db.add(new_stock)
                    inserted_count += 1

            except Exception as e:
                logger.error(f"处理记录失败: {row}, 错误: {e}")
                error_count += 1

        # 提交事务
        try:
            await self.db.commit()
            logger.info(f"数据合并完成: 插入 {inserted_count}, 更新 {updated_count}, 跳过 {skipped_count}, 错误 {error_count}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"提交事务失败: {e}")
            raise

        return {
            "inserted": inserted_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "error": error_count,
            "total": len(data)
        }

    async def update_csv_from_database(
        self,
        csv_file_path: str,
        date_column: str = "trade_date",
        code_column: str = "code",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        从数据库更新CSV文件
        
        Args:
            csv_file_path: CSV文件路径
            date_column: 日期列名
            code_column: 股票代码列名
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            更新结果统计
        """
        # 查询数据库
        stmt = select(StockDaily)
        
        if start_date:
            stmt = stmt.where(StockDaily.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(StockDaily.trade_date <= end_date)
        
        stmt = stmt.order_by(StockDaily.trade_date.desc(), StockDaily.code)
        
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        logger.info(f"从数据库查询到 {len(records)} 条记录")

        # 写入CSV文件
        fieldnames = [
            code_column,
            date_column,
            "open", "close", "high", "low",
            "vol", "amount",
            "turnover_rate", "volume_ratio", "adj_factor"
        ]

        with open(csv_file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for record in records:
                row = {
                    code_column: record.code,
                    date_column: record.trade_date.strftime("%Y-%m-%d"),
                    "open": str(record.open) if record.open else "",
                    "close": str(record.close) if record.close else "",
                    "high": str(record.high) if record.high else "",
                    "low": str(record.low) if record.low else "",
                    "vol": str(record.vol) if record.vol else "",
                    "amount": str(record.amount) if record.amount else "",
                    "turnover_rate": str(record.turnover_rate) if record.turnover_rate else "",
                    "volume_ratio": str(record.volume_ratio) if record.volume_ratio else "",
                    "adj_factor": str(record.adj_factor) if record.adj_factor else ""
                }
                writer.writerow(row)

        logger.info(f"CSV文件已更新: {csv_file_path}")

        return {
            "total": len(records),
            "file_path": csv_file_path
        }

    async def merge_tushare_data(
        self,
        tushare_data: List[Dict[str, Any]],
        keep_latest: bool = True,
        csv_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        合并Tushare数据到数据库
        
        Args:
            tushare_data: Tushare返回的数据列表
            keep_latest: 是否保留最新数据
            csv_file_path: CSV文件路径（可选，如果提供则更新CSV）
            
        Returns:
            合并结果统计
        """
        # Tushare数据字段映射
        mapped_data = []
        for item in tushare_data:
            mapped_item = {
                "code": item.get("ts_code", ""),
                "trade_date": item.get("trade_date", ""),
                "open": item.get("open"),
                "close": item.get("close"),
                "high": item.get("high"),
                "low": item.get("low"),
                "vol": item.get("vol"),
                "amount": item.get("amount"),
                "turnover_rate": item.get("turnover_rate"),
                "volume_ratio": None,
                "adj_factor": item.get("adj_factor")
            }
            mapped_data.append(mapped_item)

        # 合并到数据库
        result = await self.merge_data_to_database(
            data=mapped_data,
            date_column="trade_date",
            code_column="code",
            keep_latest=keep_latest
        )

        # 如果需要更新CSV文件
        if csv_file_path:
            await self.update_csv_from_database(csv_file_path=csv_file_path)

        return result

    async def merge_akshare_data(
        self,
        akshare_data: List[Dict[str, Any]],
        keep_latest: bool = True,
        csv_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        合并akshare数据到数据库
        
        Args:
            akshare_data: akshare返回的数据列表
            keep_latest: 是否保留最新数据
            csv_file_path: CSV文件路径（可选，如果提供则更新CSV）
            
        Returns:
            合并结果统计
        """
        # akshare数据字段映射
        mapped_data = []
        for item in akshare_data:
            mapped_item = {
                "code": item.get("股票代码", ""),
                "trade_date": item.get("日期", ""),
                "open": item.get("开盘"),
                "close": item.get("收盘"),
                "high": item.get("最高"),
                "low": item.get("最低"),
                "vol": item.get("成交量"),
                "amount": item.get("成交额"),
                "turnover_rate": item.get("换手率"),
                "volume_ratio": None,
                "adj_factor": None
            }
            mapped_data.append(mapped_item)

        # 合并到数据库
        result = await self.merge_data_to_database(
            data=mapped_data,
            date_column="trade_date",
            code_column="code",
            keep_latest=keep_latest
        )

        # 如果需要更新CSV文件
        if csv_file_path:
            await self.update_csv_from_database(csv_file_path=csv_file_path)

        return result

    async def deduplicate_by_date(
        self,
        code: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        按日期去重，保留最新数据
        
        Args:
            code: 股票代码（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            去重结果统计
        """
        # 查询重复数据
        from sqlalchemy import func
        
        stmt = select(
            StockDaily.code,
            StockDaily.trade_date,
            func.count(StockDaily.id).label('count')
        ).group_by(
            StockDaily.code,
            StockDaily.trade_date
        ).having(
            func.count(StockDaily.id) > 1
        )
        
        if code:
            stmt = stmt.where(StockDaily.code == code)
        if start_date:
            stmt = stmt.where(StockDaily.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(StockDaily.trade_date <= end_date)
        
        result = await self.db.execute(stmt)
        duplicates = result.all()

        logger.info(f"发现 {len(duplicates)} 组重复数据")

        deleted_count = 0
        for dup in duplicates:
            # 查询该股票和日期的所有记录
            stmt = select(StockDaily).where(
                StockDaily.code == dup.code,
                StockDaily.trade_date == dup.trade_date
            ).order_by(StockDaily.id.desc())
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            # 保留第一条（最新的），删除其余的
            for record in records[1:]:
                await self.db.delete(record)
                deleted_count += 1

        # 提交事务
        try:
            await self.db.commit()
            logger.info(f"去重完成，删除了 {deleted_count} 条重复记录")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"提交事务失败: {e}")
            raise

        return {
            "duplicate_groups": len(duplicates),
            "deleted": deleted_count
        }

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """解析Decimal值"""
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """解析整数值"""
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    async def merge_stock_smart(
        self,
        stock_code: str,
        source: Optional[str] = None,
        target_date: Optional[str] = None,
        force_sync: bool = False
    ) -> Dict[str, Any]:
        """
        智能数据合并（自动判断日期、避免重复）
        
        Args:
            stock_code: 股票代码
            source: 数据源（可选：csv/tushare/akshare，不指定则自动判断）
            target_date: 目标日期（可选，用于补全特定日期数据，格式：YYYYMMDD）
            force_sync: 强制同步（忽略日期检查）
            
        Returns:
            合并结果统计
        """
        # 1. 获取CSV最新日期
        csv_last_date = await self._get_csv_last_date(stock_code)
        
        # 2. 获取数据库最新日期
        db_last_date = await self._get_db_last_date(stock_code)
        
        logger.info(f"股票 {stock_code} - CSV最新日期: {csv_last_date}, 数据库最新日期: {db_last_date}")
        
        # 3. 判断是否需要同步
        if not force_sync and not target_date:
            # 如果没有指定目标日期，检查是否需要同步
            if csv_last_date and db_last_date and csv_last_date >= db_last_date:
                logger.info(f"股票 {stock_code} 数据已是最新，跳过同步")
                return {
                    "success": True,
                    "stock_code": stock_code,
                    "synced": False,
                    "message": "数据已是最新，无需同步",
                    "csv_last_date": str(csv_last_date) if csv_last_date else None,
                    "db_last_date": str(db_last_date) if db_last_date else None
                }
        
        # 4. 确定同步日期范围
        if target_date:
            # 指定了目标日期，只同步该日期
            sync_dates = [self._parse_date(target_date)]
        else:
            # 自动判断需要同步的日期范围
            sync_dates = await self._get_sync_dates(stock_code, csv_last_date, db_last_date)
        
        if not sync_dates:
            logger.info(f"股票 {stock_code} 无需同步的日期")
            return {
                "success": True,
                "stock_code": stock_code,
                "synced": False,
                "message": "无需同步的日期"
            }
        
        logger.info(f"股票 {stock_code} 需要同步的日期: {[str(d) for d in sync_dates]}")
        
        # 5. 根据数据源执行同步
        if source:
            data_source = source.lower()
        else:
            data_source = await self._detect_data_source(stock_code, csv_last_date)
        
        if data_source == "csv":
            result = await self._merge_from_csv_smart(stock_code, sync_dates)
        elif data_source == "tushare":
            result = await self._merge_from_api_smart(stock_code, sync_dates, "tushare")
        elif data_source == "akshare":
            result = await self._merge_from_api_smart(stock_code, sync_dates, "akshare")
        else:
            raise ValueError(f"不支持的数据源: {data_source}")
        
        result["csv_last_date"] = str(csv_last_date) if csv_last_date else None
        result["db_last_date"] = str(db_last_date) if db_last_date else None
        
        return result

    async def _get_csv_last_date(self, stock_code: str) -> Optional[date]:
        """获取CSV文件最后一行的日期"""
        csv_file_path = self._get_csv_path(stock_code)
        
        if not os.path.exists(csv_file_path):
            return None
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    return None
                
                # 获取最后一行
                last_row = rows[-1]
                
                # 尝试从不同列名获取日期
                date_str = last_row.get('交易日期') or last_row.get('trade_date')
                
                if not date_str:
                    return None
                
                # 解析日期
                return self._parse_date(date_str)
                
        except Exception as e:
            logger.error(f"获取CSV最新日期失败: {e}")
            return None

    async def _get_db_last_date(self, stock_code: str) -> Optional[date]:
        """获取数据库中该股票的最新日期"""
        try:
            from sqlalchemy import func
            
            stmt = select(func.max(StockDaily.trade_date)).where(StockDaily.code == stock_code)
            result = await self.db.execute(stmt)
            return result.scalar()
        except Exception as e:
            logger.error(f"获取数据库最新日期失败: {e}")
            return None

    async def _get_sync_dates(
        self,
        stock_code: str,
        csv_last_date: Optional[date],
        db_last_date: Optional[date]
    ) -> List[date]:
        """
        判断需要同步的日期范围
        
        逻辑：
        1. 如果CSV和数据库都没有数据，同步最近30天
        2. 如果CSV有数据但数据库没有，同步CSV的所有日期
        3. 如果数据库有数据但CSV没有，同步数据库最新日期到今天
        4. 如果都有数据，取较新的日期，同步到今天
        """
        today = datetime.now().date()
        
        # 情况1：都没有数据
        if not csv_last_date and not db_last_date:
            start_date = today - timedelta(days=30)
            return [start_date + timedelta(days=i) for i in range(30)]
        
        # 情况2：CSV有数据，数据库没有
        if csv_last_date and not db_last_date:
            # 从CSV最新日期开始，同步到今天
            return [csv_last_date + timedelta(days=i) for i in range(1, 31)]
        
        # 情况3：数据库有数据，CSV没有
        if db_last_date and not csv_last_date:
            # 从数据库最新日期开始，同步到今天
            return [db_last_date + timedelta(days=i) for i in range(1, 31)]
        
        # 情况4：都有数据，取较新的
        latest_date = max(csv_last_date, db_last_date)
        
        # 如果最新日期是今天，无需同步
        if latest_date >= today:
            return []
        
        # 从最新日期开始，同步到今天
        days_to_sync = (today - latest_date).days
        return [latest_date + timedelta(days=i) for i in range(1, days_to_sync + 1)]

    async def _detect_data_source(
        self,
        stock_code: str,
        csv_last_date: Optional[date]
    ) -> str:
        """
        自动检测数据来源
        
        判断逻辑：
        1. 如果CSV文件存在且有数据，使用CSV
        2. 否则根据股票代码格式判断是Tushare还是akshare
        """
        csv_file_path = self._get_csv_path(stock_code)
        
        # 检查CSV文件
        if os.path.exists(csv_file_path) and csv_last_date:
            return "csv"
        
        # 根据股票代码格式判断
        if '.' in stock_code:
            return "tushare"  # 000001.SZ 格式
        else:
            return "akshare"  # 000001 格式

    def _get_csv_path(self, stock_code: str) -> str:
        """获取CSV文件路径"""
        settings = get_settings()
        csv_root_path = settings.csv_data_path_stock_daily
        
        # 处理后缀
        filename = stock_code
        if not any(stock_code.endswith(suffix) for suffix in ['.SH', '.SZ', '.BJ']):
            if stock_code.startswith(('60', '68')):
                filename = f"{stock_code}.SH"
            elif stock_code.startswith(('00', '30')):
                filename = f"{stock_code}.SZ"
            elif stock_code.startswith(('43', '83', '87')):
                filename = f"{stock_code}.BJ"
        
        return os.path.join(csv_root_path, f"{filename}.csv")

    async def _merge_from_csv_smart(
        self,
        stock_code: str,
        sync_dates: List[date]
    ) -> Dict[str, Any]:
        """从CSV智能合并数据（避免重复、校验数据）"""
        csv_file_path = self._get_csv_path(stock_code)
        
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV文件不存在: {csv_file_path}")
        
        # 读取CSV文件
        csv_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 只保留指定股票的数据
                code = row.get('股票代码') or row.get('code')
                if code == stock_code:
                    csv_data.append(row)
        
        logger.info(f"从CSV文件读取到股票 {stock_code} 的 {len(csv_data)} 条记录")
        
        # 获取最近几天的数据用于校验
        recent_data = await self._get_recent_data_for_validation(stock_code, days=5)
        
        # 过滤出需要同步的日期
        sync_date_set = set(sync_dates)
        filtered_data = []
        
        for row in csv_data:
            date_str = row.get('交易日期') or row.get('trade_date')
            if not date_str:
                continue
            
            row_date = self._parse_date(date_str)
            
            # 只处理需要同步的日期
            if row_date in sync_date_set:
                # 数据校验
                if self._validate_data_consistency(row, recent_data):
                    filtered_data.append(row)
                else:
                    logger.warning(f"股票 {stock_code} 日期 {row_date} 数据校验失败，跳过")
        
        logger.info(f"过滤后剩余 {len(filtered_data)} 条记录")
        
        # 合并到数据库
        result = await self.merge_data_to_database(
            data=filtered_data,
            date_column="trade_date",
            code_column="code",
            keep_latest=True
        )
        
        # 更新CSV文件（去除重复）
        await self._deduplicate_csv(stock_code)
        
        return result

    async def _merge_from_api_smart(
        self,
        stock_code: str,
        sync_dates: List[date],
        api_type: str  # "tushare" or "akshare"
    ) -> Dict[str, Any]:
        """从API智能合并数据（避免重复、校验数据）"""
        # 获取最近几天的数据用于校验
        recent_data = await self._get_recent_data_for_validation(stock_code, days=5)
        
        # 获取CSV最新日期，用于追加数据
        csv_last_date = await self._get_csv_last_date(stock_code)
        
        merged_count = 0
        skipped_count = 0
        error_count = 0
        
        for sync_date in sync_dates:
            try:
                # 从API获取数据
                if api_type == "tushare":
                    data = await self._fetch_from_tushare_single(stock_code, sync_date)
                else:
                    data = await self._fetch_from_akshare_single(stock_code, sync_date)
                
                if not data:
                    logger.warning(f"股票 {stock_code} 日期 {sync_date} API未返回数据")
                    skipped_count += 1
                    continue
                
                # 数据校验
                if not self._validate_data_consistency(data, recent_data):
                    logger.warning(f"股票 {stock_code} 日期 {sync_date} 数据校验失败，跳过")
                    skipped_count += 1
                    continue
                
                # 检查是否已存在
                exists = await self._check_data_exists(stock_code, sync_date)
                if exists:
                    logger.info(f"股票 {stock_code} 日期 {sync_date} 数据已存在，跳过")
                    skipped_count += 1
                    continue
                
                # 合并到数据库
                if api_type == "tushare":
                    await self.merge_tushare_data(tushare_data=[data], keep_latest=True)
                else:
                    await self.merge_akshare_data(akshare_data=[data], keep_latest=True)
                
                # 追加到CSV
                await self._append_to_csv(stock_code, data)
                
                merged_count += 1
                
                # 更新recent_data，用于后续校验
                recent_data.append(data)
                
            except Exception as e:
                logger.error(f"股票 {stock_code} 日期 {sync_date} 合并失败: {e}")
                error_count += 1
        
        return {
            "merged": merged_count,
            "skipped": skipped_count,
            "error": error_count,
            "total": len(sync_dates)
        }

    async def _get_recent_data_for_validation(
        self,
        stock_code: str,
        days: int = 5
    ) -> List[Dict[str, Any]]:
        """获取最近几天的数据用于校验"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            stmt = select(StockDaily).where(
                StockDaily.code == stock_code,
                StockDaily.trade_date >= start_date,
                StockDaily.trade_date <= end_date
            ).order_by(StockDaily.trade_date.desc())
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            # 转换为字典列表
            data_list = []
            for record in records:
                data_list.append({
                    "open": float(record.open) if record.open else 0,
                    "close": float(record.close) if record.close else 0,
                    "high": float(record.high) if record.high else 0,
                    "low": float(record.low) if record.low else 0,
                    "vol": int(record.vol) if record.vol else 0,
                    "amount": float(record.amount) if record.amount else 0
                })
            
            return data_list
            
        except Exception as e:
            logger.error(f"获取最近数据失败: {e}")
            return []

    def _validate_data_consistency(
        self,
        new_data: Dict[str, Any],
        recent_data: List[Dict[str, Any]]
    ) -> bool:
        """
        数据一致性校验
        
        校验逻辑：
        1. 价格合理性：价格应该在最近几天价格的合理范围内
        2. 成交量合理性：成交量不应该异常波动
        3. 单位一致性：检查单位和最近数据是否一致
        """
        if not recent_data:
            # 没有历史数据，无法校验，直接通过
            return True
        
        # 获取最近数据的统计信息
        recent_opens = [d.get('open', 0) for d in recent_data]
        recent_closes = [d.get('close', 0) for d in recent_data]
        recent_vols = [d.get('vol', 0) for d in recent_data]
        
        avg_close = sum(recent_closes) / len(recent_closes) if recent_closes else 0
        avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 0
        
        # 获取新数据
        new_open = new_data.get('open', 0)
        new_close = new_data.get('close', 0)
        new_vol = new_data.get('vol', 0)
        
        # 1. 价格合理性校验（价格不应该偏离平均值超过50%）
        if avg_close > 0:
            price_ratio = abs(new_close - avg_close) / avg_close
            if price_ratio > 0.5:
                logger.warning(f"价格异常: 新价格 {new_close}, 平均价格 {avg_close}, 偏离 {price_ratio*100:.1f}%")
                return False
        
        # 2. 成交量合理性校验（成交量不应该异常波动超过10倍）
        if avg_vol > 0:
            vol_ratio = new_vol / avg_vol
            if vol_ratio > 10 or vol_ratio < 0.1:
                logger.warning(f"成交量异常: 新成交量 {new_vol}, 平均成交量 {avg_vol}, 比例 {vol_ratio:.1f}x")
                return False
        
        # 3. 价格逻辑校验
        if new_open <= 0 or new_close <= 0:
            logger.warning(f"价格非正数: open={new_open}, close={new_close}")
            return False
        
        # 4. High >= Low校验
        new_high = new_data.get('high', 0)
        new_low = new_data.get('low', 0)
        if new_high < new_low:
            logger.warning(f"最高价低于最低价: high={new_high}, low={new_low}")
            return False
        
        # 5. High >= Open/Close, Low <= Open/Close
        if new_high < max(new_open, new_close) or new_low > min(new_open, new_close):
            logger.warning(f"价格逻辑错误: high={new_high}, low={new_low}, open={new_open}, close={new_close}")
            return False
        
        return True

    async def _check_data_exists(
        self,
        stock_code: str,
        trade_date: date
    ) -> bool:
        """检查数据库中是否已存在该日期的数据"""
        try:
            stmt = select(StockDaily).where(
                StockDaily.code == stock_code,
                StockDaily.trade_date == trade_date
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"检查数据存在性失败: {e}")
            return False

    async def _append_to_csv(
        self,
        stock_code: str,
        data: Dict[str, Any]
    ):
        """追加数据到CSV文件"""
        csv_file_path = self._get_csv_path(stock_code)
        
        # 检查是否已存在该日期
        exists = await self._check_csv_date_exists(csv_file_path, data.get('trade_date') or data.get('日期'))
        if exists:
            logger.info(f"CSV中已存在该日期，跳过追加")
            return
        
        try:
            # 确定列名
            if 'ts_code' in data:
                # Tushare格式
                row = {
                    "股票代码": data['ts_code'],
                    "交易日期": self._format_date(data.get('trade_date')),
                    "开盘价": str(data.get('open', 0)),
                    "最高价": str(data.get('high', 0)),
                    "最低价": str(data.get('low', 0)),
                    "收盘价": str(data.get('close', 0)),
                    "昨收价": str(data.get('pre_close', 0)),
                    "涨跌额": str(data.get('change', 0)),
                    "涨跌幅": str(data.get('pct_chg', 0)),
                    "成交量(手)": str(data.get('vol', 0)),
                    "成交额(千元)": str(data.get('amount', 0))
                }
            else:
                # akshare格式
                row = {
                    "股票代码": data.get('股票代码'),
                    "交易日期": self._format_date(data.get('日期')),
                    "开盘价": str(data.get('开盘', 0)),
                    "最高价": str(data.get('最高', 0)),
                    "最低价": str(data.get('最低', 0)),
                    "收盘价": str(data.get('收盘', 0)),
                    "昨收价": str(data.get('pre_close', 0)),
                    "涨跌额": str(data.get('change', 0)),
                    "涨跌幅": str(data.get('pct_chg', 0)),
                    "成交量(手)": str(data.get('成交量', 0)),
                    "成交额(千元)": str(data.get('成交额', 0))
                }
            
            # 追加到CSV
            with open(csv_file_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                # 如果文件是空的，写入表头
                if os.path.getsize(csv_file_path) == 0:
                    writer.writeheader()
                writer.writerow(row)
            
            logger.info(f"数据已追加到CSV: {csv_file_path}")
        
        except Exception as e:
            logger.error(f"追加数据到CSV失败: {e}")
            raise

    async def _check_csv_date_exists(
        self,
        csv_file_path: str,
        trade_date: Any
    ) -> bool:
        """检查CSV中是否已存在该日期"""
        if not os.path.exists(csv_file_path):
            return False
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    date_str = row.get('交易日期') or row.get('trade_date')
                    if date_str == self._format_date(trade_date):
                        return True
            return False
        except Exception as e:
            logger.error(f"检查CSV日期存在性失败: {e}")
            return False

    async def _deduplicate_csv(self, stock_code: str):
        """去除CSV中的重复日期"""
        csv_file_path = self._get_csv_path(stock_code)
        
        if not os.path.exists(csv_file_path):
            return
        
        try:
            # 读取CSV
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # 去重（保留最后一条）
            seen_dates = {}
            for row in reversed(rows):
                date_str = row.get('交易日期') or row.get('trade_date')
                if date_str and date_str not in seen_dates:
                    seen_dates[date_str] = row
            
            # 按日期排序
            unique_rows = list(seen_dates.values())
            unique_rows.sort(key=lambda x: x.get('交易日期') or x.get('trade_date'))
            
            # 写回CSV
            with open(csv_file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=unique_rows[0].keys())
                writer.writeheader()
                writer.writerows(unique_rows)
            
            logger.info(f"CSV去重完成: {len(rows)} -> {len(unique_rows)}")
        
        except Exception as e:
            logger.error(f"CSV去重失败: {e}")

    async def _fetch_from_tushare_single(
        self,
        stock_code: str,
        trade_date: date
    ) -> Optional[Dict[str, Any]]:
        """从Tushare获取单个股票的单日数据"""
        try:
            from app.services.tushare_service import TushareService
            
            tushare_service = TushareService(self.db)
            date_str = trade_date.strftime("%Y%m%d")
            
            # 调用Tushare服务
            df = await tushare_service.get_daily(stock_code, date_str, date_str)
            
            if df is None or df.empty:
                return None
            
            # 转换为字典
            row = df.iloc[0]
            return {
                "ts_code": stock_code,
                "trade_date": trade_date,
                "open": float(row['open']),
                "close": float(row['close']),
                "high": float(row['high']),
                "low": float(row['low']),
                "vol": int(row['vol']),
                "amount": float(row['amount']),
                "pre_close": float(row['pre_close']) if 'pre_close' in row else 0.0,
                "change": float(row['change']) if 'change' in row else 0.0,
                "pct_chg": float(row['pct_chg']) if 'pct_chg' in row else 0.0
            }
            
        except Exception as e:
            logger.error(f"从Tushare获取数据失败: {e}")
            return None

    async def _fetch_from_akshare_single(
        self,
        stock_code: str,
        trade_date: date
    ) -> Optional[Dict[str, Any]]:
        """从akshare获取单个股票的单日数据"""
        try:
            from app.services.akshare_service import AkshareService
            
            akshare_service = AkshareService(self.db)
            date_str = trade_date.strftime("%Y-%m-%d")
            
            # 调用akshare服务
            data = await akshare_service.fetch_daily_data(stock_code, date_str, date_str)
            
            if not data:
                return None
            
            # 获取指定日期的数据
            for item in data:
                if str(item.get('trade_date')) == date_str:
                    return {
                        "股票代码": stock_code,
                        "日期": trade_date,
                        "开盘": item.get('open'),
                        "收盘": item.get('close'),
                        "最高": item.get('high'),
                        "最低": item.get('low'),
                        "成交量": item.get('vol'),
                        "成交额": item.get('amount'),
                        "pre_close": item.get('pre_close', 0.0),
                        "change": item.get('change', 0.0),
                        "pct_chg": item.get('pct_chg', 0.0)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"从akshare获取数据失败: {e}")
            return None

    def _parse_date(self, date_str: str) -> date:
        """解析日期字符串"""
        if not date_str:
            return None
        
        # 尝试不同的格式
        formats = ["%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"无法解析日期: {date_str}")

    def _format_date(self, date_obj: Any) -> str:
        """格式化日期"""
        if isinstance(date_obj, date):
            return date_obj.strftime("%Y-%m-%d")
        elif isinstance(date_obj, str):
            # 尝试解析后格式化
            try:
                dt = self._parse_date(date_obj)
                return dt.strftime("%Y-%m-%d")
            except:
                return date_obj
        else:
            return str(date_obj)
