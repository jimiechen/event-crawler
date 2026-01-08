#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pathway量价计算引擎
仅作为计算层，数据持久化仍使用现有机制
"""

from datetime import timedelta, date
from typing import Dict, List, Any, Callable, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.models.stock_daily import StockDaily
from app.models.stock_score_result import StockScoreResult
from app.models.stock import StockInfo


class PathwayVolumePriceEngine:
    """Pathway量价计算引擎（仅计算层）"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.split_date = date.fromisoformat("2025-12-22")

    async def process_new_data(self, stock_daily: StockDaily):
        """处理新数据并计算评分"""
        try:
            symbol = stock_daily.code
            trade_date = stock_daily.trade_date

            logger.info(f"Pathway处理新数据: {symbol} {trade_date}")

            tags = self._detect_tags(stock_daily)
            tag_score = self._calculate_tag_score(tags)
            total_score = tag_score

            await self._save_score_result(symbol, trade_date, tags, total_score)
            await self._aggregate_to_stock_info(symbol, trade_date, total_score)

            logger.info(f"Pathway计算完成: {symbol} {trade_date} 评分={total_score} 标签={len(tags)}")

            return {
                'symbol': symbol,
                'trade_date': trade_date,
                'tags': tags,
                'tag_score': tag_score,
                'total_score': total_score
            }

        except Exception as e:
            logger.error(f"Pathway处理数据失败: {e}")
            raise

    def _detect_tags(self, stock_daily: StockDaily) -> List[Dict[str, Any]]:
        """检测标签"""
        tags = []

        if not stock_daily or not stock_daily.open or not stock_daily.close:
            return tags

        symbol = stock_daily.code
        trade_date = stock_daily.trade_date
        open_price = float(stock_daily.open)
        close_price = float(stock_daily.close)
        high_price = float(stock_daily.high)
        low_price = float(stock_daily.low)
        volume = int(stock_daily.vol) if stock_daily.vol else 0

        tags.append({
            'name': 'basic_info',
            'value': {
                'open': open_price,
                'close': close_price,
                'high': high_price,
                'low': low_price,
                'volume': volume
            },
            'score': 0
        })

        return tags

    async def _detect_tags_with_history(self, symbol: str, trade_date: date) -> List[Dict[str, Any]]:
        """检测标签（需要历史数据）"""
        tags = []

        try:
            stmt = select(StockDaily).where(
                StockDaily.symbol == symbol,
                StockDaily.trade_date <= trade_date
            ).order_by(StockDaily.trade_date.desc()).limit(60)

            result = await self.db_session.execute(stmt)
            history = result.scalars().all()

            if len(history) < 2:
                return tags

            sorted_history = sorted(history, key=lambda x: x.trade_date, reverse=True)
            today = sorted_history[0]

            if len(sorted_history) >= 2:
                yesterday = sorted_history[1]
                volume_ratio = today.vol / yesterday.vol if yesterday.vol and yesterday.vol > 0 else 0

                if volume_ratio >= 2.8:
                    tags.append({
                        'name': '3倍量',
                        'value': volume_ratio,
                        'score': 300
                    })
                elif volume_ratio >= 2.0:
                    tags.append({
                        'name': '2倍量',
                        'value': volume_ratio,
                        'score': 200
                    })

            if len(sorted_history) >= 2:
                yesterday = sorted_history[1]
                if (today.close > today.open and
                    yesterday.close < yesterday.open and
                    today.close > yesterday.open and
                    today.open < yesterday.close):
                    tags.append({
                        'name': '阳包阴',
                        'value': (today.close - today.open) / today.open if today.open > 0 else 0,
                        'score': 200
                    })

            if len(sorted_history) >= 3:
                d1 = sorted_history[0]
                d2 = sorted_history[1]
                d3 = sorted_history[2]

                if (d2.low < d1.low and d2.low < d3.low and
                    d2.high < d1.high and d2.high < d3.high):
                    tags.append({
                        'name': '底分型',
                        'value': d2.low,
                        'score': 300
                    })

            volumes = [d.vol for d in sorted_history if d.vol]

            if len(volumes) >= 5:
                min_5 = min(volumes[:5])
                if today.vol <= min_5 * 1.1:
                    tags.append({
                        'name': '5日地量',
                        'value': today.vol / min_5 if min_5 > 0 else 0,
                        'score': 50
                    })

            if len(volumes) >= 10:
                min_10 = min(volumes[:10])
                if today.vol <= min_10 * 1.1:
                    tags.append({
                        'name': '10日地量',
                        'value': today.vol / min_10 if min_10 > 0 else 0,
                        'score': 100
                    })

            if len(volumes) >= 20:
                min_20 = min(volumes[:20])
                if today.vol <= min_20 * 1.1:
                    tags.append({
                        'name': '20日地量',
                        'value': today.vol / min_20 if min_20 > 0 else 0,
                        'score': 200
                    })

            if len(volumes) >= 30:
                min_30 = min(volumes[:30])
                if today.vol <= min_30 * 1.1:
                    tags.append({
                        'name': '30日地量',
                        'value': today.vol / min_30 if min_30 > 0 else 0,
                        'score': 300
                    })

            if len(volumes) >= 60:
                min_60 = min(volumes[:60])
                if today.vol <= min_60 * 1.1:
                    tags.append({
                        'name': '60日地量',
                        'value': today.vol / min_60 if min_60 > 0 else 0,
                        'score': 600
                    })

        except Exception as e:
            logger.error(f"检测标签失败 {symbol} {trade_date}: {e}")

        return tags

    def _calculate_tag_score(self, tags: List[Dict[str, Any]]) -> float:
        """计算标签总分"""
        return sum(tag.get('score', 0) for tag in tags)

    async def _save_score_result(self, symbol: str, trade_date: date, tags: List[Dict[str, Any]], total_score: float):
        """保存评分结果到数据库"""
        try:
            stmt = select(StockScoreResult).where(
                StockScoreResult.code == symbol,
                StockScoreResult.trade_date == trade_date
            )

            result = await self.db_session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.rule_scores = tags
                existing.total_score = total_score
            else:
                score_result = StockScoreResult(
                    code=symbol,
                    trade_date=trade_date,
                    rule_scores=tags,
                    total_score=total_score
                )
                self.db_session.add(score_result)

            await self.db_session.commit()
            logger.debug(f"保存评分结果: {symbol} {trade_date} {total_score}")

        except Exception as e:
            logger.error(f"保存评分结果失败: {e}")
            await self.db_session.rollback()
            raise

    async def _aggregate_to_stock_info(self, symbol: str, trade_date: date, total_score: float):
        """聚合到 stock_info.volume_anomaly_score"""
        try:
            start_date = trade_date - timedelta(days=250)

            stmt = select(
                func.sum(StockScoreResult.total_score)
            ).where(
                StockScoreResult.code == symbol,
                StockScoreResult.trade_date >= start_date,
                StockScoreResult.trade_date <= trade_date
            )

            result = await self.db_session.execute(stmt)
            total_250_days = result.scalar() or 0.0

            update_stmt = (
                update(StockInfo)
                .where(StockInfo.code == symbol)
                .values(
                    volume_anomaly_score=int(total_250_days),
                    score_update_time=trade_date
                )
            )

            await self.db_session.execute(update_stmt)
            await self.db_session.commit()
            logger.debug(f"聚合到stock_info: {symbol} {trade_date} {total_250_days}")

        except Exception as e:
            logger.error(f"聚合到stock_info失败: {e}")
            await self.db_session.rollback()
            raise

    async def calculate_score_for_date(self, symbol: str, trade_date: date) -> Optional[Dict[str, Any]]:
        """为指定日期计算评分"""
        try:
            stmt = select(StockDaily).where(
                StockDaily.symbol == symbol,
                StockDaily.trade_date == trade_date
            )

            result = await self.db_session.execute(stmt)
            stock_daily = result.scalar_one_or_none()

            if not stock_daily:
                logger.warning(f"未找到数据: {symbol} {trade_date}")
                return None

            return await self.process_new_data(stock_daily)

        except Exception as e:
            logger.error(f"计算评分失败 {symbol} {trade_date}: {e}")
            return None

    async def batch_calculate_scores(self, symbol: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """批量计算评分"""
        results = []

        try:
            stmt = select(StockDaily).where(
                StockDaily.symbol == symbol,
                StockDaily.trade_date >= start_date,
                StockDaily.trade_date <= end_date
            ).order_by(StockDaily.trade_date)

            result = await self.db_session.execute(stmt)
            stock_dailies = result.scalars().all()

            for stock_daily in stock_dailies:
                result = await self.process_new_data(stock_daily)
                if result:
                    results.append(result)

            logger.info(f"批量计算完成: {symbol} {len(results)}条记录")

        except Exception as e:
            logger.error(f"批量计算失败 {symbol}: {e}")

        return results
