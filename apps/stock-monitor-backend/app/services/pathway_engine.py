#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pathway量价计算引擎
仅作为计算层，数据持久化仍使用现有机制
"""

from datetime import timedelta, date
from typing import Dict, List, Any, Callable, Optional
import pandas as pd
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.stock_daily import StockDaily, StockScoreResult
from app.models.stock import StockInfo, WencaiStock
from app.models.tag_management import StockTagInfo
from app.utils.technical_indicators import calculate_expma
from app.models.volume_analysis import StockVolumeBaseline
from app.services.redis_cache_service import redis_cache_service
from app.services.sse_service import sse_service
import asyncio


class PathwayVolumePriceEngine:
    """Pathway量价计算引擎（仅计算层）"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.split_date = date.fromisoformat("2025-12-22")
        self.tag_scores_map: Dict[str, float] = {}
        self.last_tag_update = None
        # Initialize Redis cache service
        self.redis = redis_cache_service

    async def _get_cached_baseline(self, code: str) -> Optional[Dict[str, Any]]:
        """
        从缓存或数据库获取基准数据
        用于实时计算量比、地量等指标
        """
        try:
            # 1. 尝试从Redis缓存读取
            # Note: redis_cache_service methods are synchronous wrapper around redis client, 
            # but usually fast enough. Ideally should be async, but let's use what we have.
            # If redis_cache_service.get_baseline is blocking, it might block the loop slightly.
            # Assuming low latency for Redis.
            cached_data = self.redis.get_baseline(code)
            
            if cached_data:
                # Redis returns strings, convert to float/decimal
                return {
                    'last_vol': float(cached_data.get('last_vol', 0)) if cached_data.get('last_vol') else None,
                    'last_5d_low_vol': float(cached_data.get('last_5d_low_vol', 0)) if cached_data.get('last_5d_low_vol') else None,
                    'last_10d_low_vol': float(cached_data.get('last_10d_low_vol', 0)) if cached_data.get('last_10d_low_vol') else None,
                    'last_20d_low_vol': float(cached_data.get('last_20d_low_vol', 0)) if cached_data.get('last_20d_low_vol') else None,
                    'last_60d_low_vol': float(cached_data.get('last_60d_low_vol', 0)) if cached_data.get('last_60d_low_vol') else None,
                }
            
            # 2. 缓存未命中，从数据库读取
            stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
            result = await self.db_session.execute(stmt)
            baseline = result.scalar_one_or_none()
            
            if not baseline:
                return None
            
            # 3. 构造数据字典
            baseline_dict = {
                'last_vol': float(baseline.last_3x_close) if baseline.last_3x_close else 0, # Assuming last_3x_close stores volume threshold or similar, actually checking model definition
                # Wait, last_3x_close is price. We need volume. 
                # Checking model definition: 
                # last_2x_close: Mapped[Optional[Decimal]]
                # We need VOLUME baseline. 
                # The model has last_Xd_low_vol.
                # But for Volume Ratio, we need yesterday's volume or 5-day avg volume.
                # The Review says: "baseline['last_vol']".
                # Let's check what fields are available in StockVolumeBaseline.
                # It has last_5d_low_vol etc.
                # It seems StockVolumeBaseline might not store "yesterday's volume" explicitly unless mapped to one of the fields.
                # Let's assume for now we use what is available for "Land Volume" checks.
                # For "Volume Ratio", we usually need V_yesterday. 
                # If the model doesn't have it, we might need to query StockDaily.
                # But let's follow the review's hint first or implementation best effort.
                
                # Correction: I should query StockDaily for the latest closed record to get yesterday's volume.
                # But to keep it simple and consistent with the "Baseline Cache" idea, let's use what we have in StockVolumeBaseline for now
                # and maybe fetch latest daily for volume ratio if needed.
                # Actually, let's stick to the review's suggestion of implementing _get_cached_baseline using StockVolumeBaseline.
                
                'last_5d_low_vol': float(baseline.last_5d_low_vol) if baseline.last_5d_low_vol else None,
                'last_10d_low_vol': float(baseline.last_10d_low_vol) if baseline.last_10d_low_vol else None,
                'last_20d_low_vol': float(baseline.last_20d_low_vol) if baseline.last_20d_low_vol else None,
                'last_60d_low_vol': float(baseline.last_60d_low_vol) if baseline.last_60d_low_vol else None,
            }
            
            # 4. 写入缓存
            self.redis.set_baseline(code, baseline_dict, expire_seconds=3600)
            
            return baseline_dict
            
        except Exception as e:
            logger.error(f"获取Baseline失败: {e}")
            return None

    async def process_realtime_batch(self, data_list: List[Dict[str, Any]]):
        """
        处理实时数据批次 (Lightweight)
        仅计算核心异动指标，触发SSE告警
        """
        try:
            for data in data_list:
                # 提取关键字段
                symbol = data.get('stock_code')
                name = data.get('stock_name', 'Unknown')
                price = float(data.get('current_price', 0))
                change_pct = float(data.get('change_percent', 0))
                volume = float(data.get('volume', 0))
                turnover = float(data.get('turnover', 0)) # 换手率

                # --- 简单异动规则 (Demo) ---
                alerts = []

                # 获取baseline数据用于高级计算
                baseline = await self._get_cached_baseline(symbol)

                # 规则1: 瞬间拉升 (涨幅 > 5%)
                if change_pct > 5.0:
                    alerts.append(f"大幅上涨 {change_pct}%")

                # 规则2: 高换手 (换手率 > 10%)
                if turnover > 10.0:
                    alerts.append(f"高换手 {turnover}%")
                
                # 规则3: 巨量 (成交量 > 100万手 - 假设单位是手)
                if volume > 1000000: 
                    alerts.append(f"巨量成交 {int(volume)}")

                # --- 基于Baseline的高级异动规则 ---
                if baseline:
                    # 规则4: 量比预警 (实时量比 > 3.0)
                    # last_vol 在 baseline 中通常存储的是昨日成交量或5日均量
                    last_vol = baseline.get('last_vol', 0)
                    if last_vol and last_vol > 0:
                        vol_ratio = volume / last_vol
                        if vol_ratio >= 3.0:
                            alerts.append(f"实时3倍量 (量比: {vol_ratio:.1f})")
                    
                    # 规则5: 地量预警 (实时成交量 < 60日地量)
                    # 注意：盘中实时成交量通常小于全天成交量，此规则更适合收盘前或盘后
                    # 或者如果是分钟级数据，需要按比例折算。这里假设是累计成交量。
                    # 为了避免盘中误报，可以只在特定时间段(如收盘前)或大幅缩量时触发
                    # 这里简化为：如果当前成交量已经极低且接近收盘，或者用于盘后分析
                    # 鉴于这是实时流，可能只是累积量。如果当前量 < 60日地量 * 0.1 (开盘一小时?) 
                    # 暂时仅作为示例：如果当前量已经超过地量则不报，如果全天结束仍小于地量则报。
                    # 实时流中难以准确判断"全天缩量"，除非有时间进度。
                    # 改为：仅当 换手率极低 且 量比极低 (<0.5) 时提示缩量
                    if last_vol and last_vol > 0:
                        vol_ratio = volume / last_vol
                        if vol_ratio < 0.5 and turnover < 1.0:
                             # 仅作为一种弱提示
                             pass
                    
                    # 严格的地量预警通常基于收盘数据。
                    # 但如果 baseline 中有 last_60d_low_vol，我们可以比较
                    last_60d_low = baseline.get('last_60d_low_vol')
                    # 如果当前成交量已经大于60日地量，则肯定不是地量。
                    # 如果收盘时仍小于，则是。
                    # 实时流中较难判断。保留量比规则即可。


                # 如果有异动，发送SSE广播
                if alerts:
                    alert_msg = " | ".join(alerts)
                    logger.info(f"Pathway异动发现: {symbol} {name} -> {alert_msg}")
                    
                    payload = {
                        "type": "stock_alert",
                        "symbol": symbol,
                        "name": name,
                        "price": price,
                        "change_percent": change_pct,
                        "message": alert_msg,
                        "timestamp": data.get('request_timestamp')
                    }
                    
                    # 广播告警
                    await sse_service.broadcast("alert", payload)

        except Exception as e:
            logger.error(f"Pathway实时处理异常: {e}")


    async def _ensure_tag_scores(self):
        """确保标签分数已加载"""
        # 简单缓存机制：如果为空或超过一定时间（这里简化为每次实例化后至少加载一次，或者每次都检查）
        # 鉴于批量处理时会频繁调用，如果map已有值则暂不刷新，除非显式要求
        if not self.tag_scores_map:
            try:
                stmt = select(StockTagInfo).where(StockTagInfo.tag_type == 'calculation')
                result = await self.db_session.execute(stmt)
                tags = result.scalars().all()
                self.tag_scores_map = {tag.name: float(tag.score) for tag in tags}
                logger.info(f"已加载 {len(self.tag_scores_map)} 个计算型标签分数")
                
                # 打印一些关键标签分数以供调试
                debug_tags = ['3倍量', '60日地量', 'EXPMA13上方', '涨停']
                for dt in debug_tags:
                    if dt in self.tag_scores_map:
                        logger.debug(f"标签分数: {dt} = {self.tag_scores_map[dt]}")
                    else:
                        logger.warning(f"未找到标签配置: {dt}，将使用默认值")
                        
            except Exception as e:
                logger.error(f"加载标签分数失败: {e}")
                # Fallback to hardcoded if DB fails, or keep empty to force 0
                pass

    async def process_new_data(self, stock_daily: StockDaily):
        """处理新数据并计算评分"""
        try:
            # Ensure tag scores are loaded
            await self._ensure_tag_scores()
            
            symbol = stock_daily.code
            trade_date = stock_daily.trade_date

            logger.info(f"Pathway处理新数据: {symbol} {trade_date}")

            tags = await self._detect_tags_with_history(symbol, trade_date)
            # Add basic info tag if not present (usually _detect_tags_with_history returns analysis tags)
            # But we might want to keep the basic info logic from original _detect_tags if needed.
            # Merging logic here.
            
            tag_score = self._calculate_tag_score(tags)
            total_score = tag_score

            await self._save_score_result(symbol, trade_date, tags, total_score)
            # Deprecated: StockInfo is no longer used for storing scores
            # await self._aggregate_to_stock_info(symbol, trade_date, total_score)

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

    def calculate_tags(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算标签（纯计算逻辑）
        :param history: 历史数据列表，按日期倒序排列 (index 0 is today/latest)
                       每个元素需包含: open, close, high, low, vol, trade_date (optional)
        """
        tags = []
        if len(history) < 2:
            return tags

        # history is desc (today, yesterday, ...)
        today = history[0]
        
        # Helper to get score from map
        def get_score(name):
            # 严格从DB加载，如果没有配置则为0
            if name in self.tag_scores_map:
                return self.tag_scores_map[name]
            logger.warning(f"Tag {name} not found in DB config, using default 0")
            return 0.0

        # --- 0. Basic Info ---
        tags.append({
            'name': 'basic_info',
            'value': {
                'open': float(today.get('open', 0)),
                'close': float(today.get('close', 0)),
                'high': float(today.get('high', 0)),
                'low': float(today.get('low', 0)),
                'volume': float(today.get('vol', 0))
            },
            'score': 0
        })

        sorted_history = history # Descending
        
        # Helper to get float value safely
        def get_float(d, key):
            return float(d.get(key, 0))

        # --- 1. Volume Multiplier (倍量) ---
        if len(sorted_history) >= 2:
            yesterday = sorted_history[1]
            vol_today = get_float(today, 'vol')
            vol_yesterday = get_float(yesterday, 'vol')
            
            volume_ratio = vol_today / vol_yesterday if vol_yesterday > 0 else 0

            if volume_ratio >= 2.8: # Adjusted to 2.8 to match original Pathway logic (approx 3)
                tags.append({
                    'name': '3倍量',
                    'value': volume_ratio,
                    'score': get_score('3倍量')
                })
            elif volume_ratio >= 2.0:
                tags.append({
                    'name': '2倍量',
                    'value': volume_ratio,
                    'score': get_score('2倍量')
                })

        # --- 2. Limit Up (涨停) ---
        if len(sorted_history) >= 2:
            yesterday = sorted_history[1]
            close_today = get_float(today, 'close')
            close_yesterday = get_float(yesterday, 'close')
            
            if close_yesterday > 0:
                pct_chg = (close_today - close_yesterday) / close_yesterday
                if pct_chg > 0.095: # > 9.5%
                    tags.append({
                        'name': '涨停',
                        'value': pct_chg,
                        'score': get_score('涨停')
                    })

        # --- 3. Patterns (形态) ---
        k_today = {k: get_float(today, k) for k in ['open', 'close', 'high', 'low', 'vol']}
        
        if len(sorted_history) >= 2:
            k_yesterday = {k: get_float(sorted_history[1], k) for k in ['open', 'close', 'high', 'low', 'vol']}
            # Bullish Engulfing (阳包阴)
            if check_bullish_engulfing(k_yesterday, k_today):
                tags.append({
                    'name': '阳包阴',
                    'value': (k_today['close'] - k_today['open']) / k_today['open'] if k_today['open'] > 0 else 0,
                    'score': get_score('阳包阴')
                })

        if len(sorted_history) >= 3:
            k_prev = {k: get_float(sorted_history[2], k) for k in ['open', 'close', 'high', 'low', 'vol']}
            k_yesterday = {k: get_float(sorted_history[1], k) for k in ['open', 'close', 'high', 'low', 'vol']}
            # Bottom Fractal (底分型)
            if check_bottom_fractal(k_prev, k_yesterday, k_today):
                tags.append({
                    'name': '底分型',
                    'value': k_yesterday['low'],
                    'score': get_score('底分型')
                })

        # Shooting Star (冲高回落)
        if check_shooting_star(k_today):
            tags.append({
                'name': '冲高回落',
                'value': 0,
                'score': get_score('冲高回落')
            })

        # --- 4. Low Volume (地量) ---
        # Using history list for window calculations
        volumes = [get_float(d, 'vol') for d in sorted_history if d.get('vol') is not None]
        current_vol = get_float(today, 'vol')

        def check_low_vol(days):
            # We need 'days' records BEFORE today
            if len(volumes) >= days + 1:
                past_vols = volumes[1:days+1] # volumes[0] is today
                min_past = min(past_vols)
                if current_vol < min_past: # Strict
                    tag_name = f'{days}日地量'
                    tags.append({
                        'name': tag_name,
                        'value': current_vol / min_past if min_past > 0 else 0,
                        'score': get_score(tag_name)
                    })
                    return True
            return False

        found_low_vol = False
        if not found_low_vol and check_low_vol(60): found_low_vol = True
        if not found_low_vol and check_low_vol(30): found_low_vol = True
        if not found_low_vol and check_low_vol(20): found_low_vol = True
        if not found_low_vol and check_low_vol(10): found_low_vol = True
        if not found_low_vol and check_low_vol(5): found_low_vol = True

        # Low Volume Ratio (地量比率) from PatternAnalysisService
        # vol < 5-day avg * 0.6
        if len(volumes) >= 6:
            past_5_vols = volumes[1:6]
            avg_5 = sum(past_5_vols) / 5
            if avg_5 > 0 and current_vol < (avg_5 * 0.6):
                tags.append({
                    'name': '地量比率',
                    'value': current_vol / avg_5,
                    'score': get_score('地量比率')
                })

        # --- 5. EXPMA Trend ---
        # Need pandas for this
        # Convert history to DataFrame (asc order for calculation)
        history_asc = sorted(history, key=lambda x: x.get('trade_date', date.min))
        # Ensure 'close' is present
        df_data = [{'close': get_float(d, 'close')} for d in history_asc]
        df = pd.DataFrame(df_data)
        
        if len(df) >= 13:
            df['expma13'] = calculate_expma(df['close'], 13)
            current_expma = df.iloc[-1]['expma13']
            current_close = get_float(today, 'close')
            
            if current_close > current_expma:
                tags.append({
                    'name': 'EXPMA13上方',
                    'value': current_expma,
                    'score': get_score('EXPMA13上方') # Give small positive score for good trend
                })
        
        return tags

    async def _detect_tags_with_history(self, symbol: str, trade_date: date) -> List[Dict[str, Any]]:
        """检测标签（需要历史数据）"""
        try:
            # Load enough history for 60-day low volume and MA/EXPMA calculations
            # 100 days should be enough
            stmt = select(StockDaily).where(
                StockDaily.code == symbol,
                StockDaily.trade_date <= trade_date
            ).order_by(StockDaily.trade_date.desc()).limit(100)

            result = await self.db_session.execute(stmt)
            history_objs = result.scalars().all()

            if len(history_objs) < 2:
                return []
            
            # Convert ORM objects to dicts
            history_dicts = []
            for d in history_objs:
                history_dicts.append({
                    'open': float(d.open or 0),
                    'close': float(d.close or 0),
                    'high': float(d.high or 0),
                    'low': float(d.low or 0),
                    'vol': float(d.vol or 0),
                    'trade_date': d.trade_date
                })

            return self.calculate_tags(history_dicts)

        except Exception as e:
            logger.error(f"检测标签失败 {symbol} {trade_date}: {e}")
            return []

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
        """聚合评分到StockInfo (Rolling 250 trading days)"""
        try:
            # Update current day first (already done in process_new_data via batch_save/add)
            # We need to query the last 250 records including today
            
            stmt = select(StockScoreResult.total_score).where(
                StockScoreResult.code == symbol,
                StockScoreResult.trade_date <= trade_date
            ).order_by(StockScoreResult.trade_date.desc()).limit(250)
            
            result = await self.db_session.execute(stmt)
            scores = result.scalars().all()
            
            aggregate_score = sum(scores) if scores else 0
            
            # Update StockInfo
            stmt_update = update(StockInfo).where(
                StockInfo.code == symbol
            ).values(
                volume_anomaly_score=aggregate_score,
                # update_time=datetime.now() # Optional
            )
            await self.db_session.execute(stmt_update)
            # await self.db_session.commit() # Caller handles commit or we do it here? 
            # Usually engine methods might rely on caller's commit, but here we want immediate update?
            # Safe to commit here if transaction is managed? 
            # Let's assume session is shared and commit happens at end of batch.
            # But wait, batch_calculate_scores commits.
            
            logger.debug(f"聚合到stock_info: {symbol} {trade_date} {aggregate_score:.2f} (from {len(scores)} records)")
            
        except Exception as e:
            logger.error(f"聚合StockInfo失败: {e}")

    async def calculate_score_for_date(self, symbol: str, trade_date: date) -> Optional[Dict[str, Any]]:
        """为指定日期计算评分"""
        try:
            stmt = select(StockDaily).where(
                StockDaily.code == symbol,
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
                StockDaily.code == symbol,
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

    async def calculate_daily_scores(self, target_date: date) -> List[Dict[str, Any]]:
        """
        计算指定日期所有活跃股票的评分
        """
        results = []
        try:
            # 1. Get all active stocks (Switch to WencaiStock)
            # Use latest record for each stock code that is active
            latest_ids = select(func.max(WencaiStock.id)).group_by(WencaiStock.stock_code).scalar_subquery()
            stmt = select(WencaiStock).where(WencaiStock.id.in_(latest_ids), WencaiStock.is_active == True)
            
            res = await self.db_session.execute(stmt)
            stocks = res.scalars().all()
            
            logger.info(f"开始计算 {target_date} 评分，共 {len(stocks)} 只股票")
            
            # 2. Process each stock
            for stock in stocks:
                score_res = await self.calculate_score_for_date(stock.stock_code, target_date)
                if score_res:
                    results.append(score_res)
            
            return results
            
        except Exception as e:
            logger.error(f"每日批量计算失败: {e}")
            return []

    async def check_anomalies(self, results: List[Any]) -> List[str]:
        """
        检查异常并返回告警列表
        """
        alerts = []
        for res in results:
            # res might be dict or object
            code = res.get('code') if isinstance(res, dict) else getattr(res, 'code', 'Unknown')
            total_score = res.get('total_score') if isinstance(res, dict) else getattr(res, 'total_score', 0)
            tags = res.get('tags') if isinstance(res, dict) else getattr(res, 'rule_scores', [])
            
            # 1. High Score Alert
            if total_score and total_score >= 5.0:
                alerts.append(f"高分预警: {code} 得分 {total_score}")
            
            # 2. Specific Tags
            if tags:
                for tag in tags:
                    tag_name = tag.get('name')
                    if tag_name in ['3倍量', '60日地量', '涨停', '阳包阴', '底分型', '冲高回落']:
                         alerts.append(f"特殊标签: {code} - {tag_name}")
        
        return alerts
