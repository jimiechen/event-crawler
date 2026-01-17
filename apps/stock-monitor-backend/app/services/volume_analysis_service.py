#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量异动分析服务
"""

from typing import List, Dict, Optional, Any
from datetime import date, timedelta, datetime
import json
import asyncio
from decimal import Decimal
from sqlalchemy import select, desc, delete, and_, update, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.volume_analysis import VolumeAnalysisResult, RuleCalculationLog, AlertRecord, StockVolumeBaseline
from ..models.stock_daily import StockDaily, StockScoreResult
from ..models.stock import StockInfo
from ..models.tag_management import StockTagInfo, StockTagRelation
from ..database import db_manager
from .stock_data_manager import StockDataManager
from .pathway_engine import PathwayVolumePriceEngine

from loguru import logger

class VolumeAnalysisService:
    
    # Configuration
    SCORE_WINDOW_DAYS = 250  # 总分计算窗口（天）
    HISTORY_LOAD_DAYS = 400  # 计算时加载的历史数据天数
    BASELINE_LOAD_DAYS = 100 # 前端展示/基准加载天数

    # Tag Definitions and Scores (Shared)
    TAG_SCORES = {
        '涨停': -100,
        '3倍量': 300,
        '2倍量': 200,
        '60日地量': 600,
        '30日地量': 300,
        '20日地量': 200,
        '10日地量': 100,
        '5日地量': 50
    }

    @staticmethod
    def calculate_scores_batch(df, group_col=None):
        """
        Apply volume anomaly scoring rules to a Pandas DataFrame.
        Expects columns: 'vol', 'close', 'trade_date'.
        Returns a Series with daily scores.
        """
        import pandas as pd
        import numpy as np

        # Ensure sorted
        if group_col:
            df = df.sort_values([group_col, 'trade_date'])
        else:
            df = df.sort_values('trade_date')
        
        # Calculate shifted values
        if group_col:
            grouper = df.groupby(group_col)
            df['prev_vol'] = grouper['vol'].shift(1)
            df['prev_close'] = grouper['close'].shift(1)
        else:
            df['prev_vol'] = df['vol'].shift(1)
            df['prev_close'] = df['close'].shift(1)
        
        # Initialize score
        scores = pd.Series(0, index=df.index)
        
        # 1. Volume Multiplier
        mask_valid_vol = df['prev_vol'] > 0
        ratio = pd.Series(0.0, index=df.index)
        ratio[mask_valid_vol] = df.loc[mask_valid_vol, 'vol'] / df.loc[mask_valid_vol, 'prev_vol']
        
        scores[ratio >= 3.0] += VolumeAnalysisService.TAG_SCORES['3倍量']
        scores[(ratio >= 2.0) & (ratio < 3.0)] += VolumeAnalysisService.TAG_SCORES['2倍量']
        
        # 2. Limit Up
        mask_valid_close = df['prev_close'] > 0
        pct_chg = pd.Series(0.0, index=df.index)
        pct_chg[mask_valid_close] = (df.loc[mask_valid_close, 'close'] - df.loc[mask_valid_close, 'prev_close']) / df.loc[mask_valid_close, 'prev_close']
        
        scores[pct_chg > 0.095] += VolumeAnalysisService.TAG_SCORES['涨停']
        
        # 3. Low Volume
        has_low_vol = pd.Series(False, index=df.index)
        
        windows = [
            (60, VolumeAnalysisService.TAG_SCORES['60日地量']),
            (30, VolumeAnalysisService.TAG_SCORES['30日地量']),
            (20, VolumeAnalysisService.TAG_SCORES['20日地量']),
            (10, VolumeAnalysisService.TAG_SCORES['10日地量']),
            (5, VolumeAnalysisService.TAG_SCORES['5日地量'])
        ]
        
        for window, score_val in windows:
            if group_col:
                # prev_vol is already shifted 1, so rolling(window) on it gives min of [i-1...i-window]
                past_min = df.groupby(group_col)['prev_vol'].transform(lambda x: x.rolling(window).min())
            else:
                past_min = df['prev_vol'].rolling(window).min()
            
            condition = (df['vol'] < past_min) & (~has_low_vol) & (df['vol'] > 0)
            scores[condition] += score_val
            has_low_vol = has_low_vol | condition
            
        return scores

    @staticmethod
    async def get_anomalies(code: str, start_date: date, end_date: date, session: AsyncSession) -> List[Dict[str, Any]]:
        """
        获取指定时间范围内的成交量异动分析结果 (Server-side implementation of test-tool logic)
        """
        # Ensure data is available via StockDataManager
        stock_data_manager = StockDataManager(db_manager)
        
        # Load enough history for calculation (e.g. 100 days before start_date)
        # We fetch a generous amount to cover the range + lookback
        # Note: get_stock_data syncs if needed
        # We fetch 1000 records to be safe for historical analysis, or just enough?
        # If we need specific range, StockDataManager might need a range query method, 
        # but currently get_stock_data(limit) gets latest N. 
        # For historical range far back, this might be an issue if limit is small.
        # But for "monitoring" context, usually we look at recent data.
        # Let's assume 500 is enough for now, or improve StockDataManager later.
        
        # Use existing session if possible, but StockDataManager uses its own session factory.
        # That's okay, they are read operations.
        
        all_data = await stock_data_manager.get_stock_data(code, limit=1000)
        
        if not all_data:
            return []
            
        # Filter in memory (since we want to ensure sync happened)
        # all_data is sorted desc by default from get_stock_data
        
        # Sort asc for processing
        data = sorted(all_data, key=lambda x: x.trade_date)
        
        # Filter for [start_date - 100, end_date]
        history_start = start_date - timedelta(days=100)
        data = [d for d in data if d.trade_date >= history_start and d.trade_date <= end_date]
        
        if not data:
            return []
            
        # Convert to list of dicts or objects for processing
        # We need to map the logic from JS:
        # 1. Volume Multiplier (2x, 3x)
        # 2. Limit Up (9.5%+)
        # 3. Low Volume (5, 10, 20, 30, 60 days)
        
        results = []
        
        # We need at least 1 day prior for volume multiplier
        # We process from index 1 to end
        
        # Tag Definitions and Scores (mirrors JS)
        TAG_SCORES = VolumeAnalysisService.TAG_SCORES
        
        # Color index for frontend consistency (optional, but good for UI)
        colors = [
            '#FF00FF', '#00FFFF', '#FFA500', '#00FF00', '#FF0000', '#FFFF00', 
            '#8A2BE2', '#7FFF00', '#DC143C', '#00CED1', '#FF1493', '#FFD700'
        ]
        color_idx = 0
        last_found_index = -1
        
        for i in range(1, len(data)):
            current = data[i]
            # Skip if before requested start_date
            if current.trade_date < start_date:
                continue
                
            prev = data[i-1]
            
            cur_vol = float(current.vol or 0)
            prev_vol = float(prev.vol or 0)
            cur_close = float(current.close or 0)
            prev_close = float(prev.close or 0)
            
            triggered_tags = []
            
            # 1. Volume Multiplier
            ratio = 0.0
            vol_tag = None
            if prev_vol > 0:
                ratio = cur_vol / prev_vol
                if ratio >= 3.0:
                    vol_tag = '3倍量'
                elif ratio >= 2.0:
                    vol_tag = '2倍量'
            
            if vol_tag:
                triggered_tags.append(vol_tag)
                
            # 2. Limit Up
            is_limit_up = False
            if prev_close > 0:
                pct_chg = (cur_close - prev_close) / prev_close
                if pct_chg > 0.095: # > 9.5%
                    is_limit_up = True
                    triggered_tags.append('涨停')
            
            # 3. Low Volume
            low_tags = []
            # Check windows: 60, 30, 20, 10, 5
            # JS Logic: checks in order and breaks? No, JS:
            # if (check(60)) { ... } else if (check(30)) ...
            # So only the longest period is recorded.
            
            def check_low_vol(days):
                if i < days: return False
                # slice data[i-days : i] -> past 'days' records excluding current?
                # JS: daily_data[-(days+1):-1] where current is last.
                # Here current is data[i]. So past is data[i-days : i].
                past_vols = [float(d.vol or 0) for d in data[i-days : i]]
                if not past_vols: return False
                min_past = min(past_vols)
                return cur_vol < min_past

            if check_low_vol(60): low_tags.append('60日地量')
            elif check_low_vol(30): low_tags.append('30日地量')
            elif check_low_vol(20): low_tags.append('20日地量')
            elif check_low_vol(10): low_tags.append('10日地量')
            elif check_low_vol(5): low_tags.append('5日地量')
            
            if low_tags:
                triggered_tags.extend(low_tags)
            
            if triggered_tags:
                desc_str = ", ".join(triggered_tags)
                
                # Calculate distance
                distance = '-'
                if last_found_index != -1:
                    distance = str(i - last_found_index)
                
                results.append({
                    "date": current.trade_date.isoformat(),
                    "volume": cur_vol,
                    "prevDate": prev.trade_date.isoformat(),
                    "prevVolume": prev_vol,
                    "ratio": round(ratio, 2),
                    "distance": distance,
                    "open": float(current.open or 0),
                    "close": float(current.close or 0),
                    "isLimitUp": is_limit_up,
                    "description": desc_str,
                    "color": colors[color_idx % len(colors)],
                    "visible": True,
                    "id": f"anomaly-{current.trade_date.isoformat()}"
                })
                
                color_idx += 1
                last_found_index = i
                
        # Return reversed (newest first) as per JS
        return list(reversed(results))

    @staticmethod
    async def generate_daily_tags(code: str, target_date: date, session: AsyncSession, sync_if_missing: bool = True):
        """
        生成指定日期股票的标签（基于成交量异动）
        并更新到 stock_tag_relations 表
        """
        # 1. 获取数据 (Target Date + Past 100 days)
        start_date = target_date - timedelta(days=100) 
        stock_data_manager = StockDataManager(db_manager)
        daily_data = await stock_data_manager.get_stock_data(code, start_date=start_date, end_date=target_date, sync_if_missing=sync_if_missing)
        daily_data = sorted(daily_data, key=lambda x: x.trade_date)
        
        if not daily_data:
            return
            
        # Ensure the last record is target_date
        if daily_data[-1].trade_date != target_date:
            return
            
        current = daily_data[-1]
        
        # Need at least yesterday for Volume Multiplier
        if len(daily_data) < 2:
            return
            
        prev = daily_data[-2]
        
        tags_to_add = []
        
        # --- Load Score Config ---
        stmt = select(StockTagInfo).where(StockTagInfo.tag_type == 'calculation')
        result = await session.execute(stmt)
        calc_tags = result.scalars().all()
        score_config = {tag.name: float(tag.score) for tag in calc_tags}
        
        def get_score(name, default=0):
            return score_config.get(name, default)

        # --- 1. Volume Multiplier ---
        cur_vol = float(current.vol or 0)
        prev_vol = float(prev.vol or 0)
        
        if prev_vol > 0:
            vol_ratio = cur_vol / prev_vol
            if vol_ratio >= 3.0:
                tags_to_add.append(("3倍量", get_score("3倍量", 0)))
            elif vol_ratio >= 2.0:
                tags_to_add.append(("2倍量", get_score("2倍量", 0)))
                
        # --- 2. Low Volume ---
        def check_low_vol(days):
            if len(daily_data) < days + 1:
                return False
            
            # Slice: [-(days+1) : -1]  -> Past 'days' records
            past_records = daily_data[-(days+1):-1]
            if not past_records:
                return False
                
            min_past = min([float(d.vol or 0) for d in past_records])
            return cur_vol < min_past

        # Check in order
        low_vol_configs = [
            (60, "60日地量"),
            (30, "30日地量"),
            (20, "20日地量"),
            (10, "10日地量"),
            (5, "5日地量")
        ]
        
        for days, name in low_vol_configs:
            if check_low_vol(days):
                tags_to_add.append((name, get_score(name, 0)))
                break # Only longest period
                
        # --- 3. Update DB ---
        # Get IDs of tags to add (ensure they exist)
        tag_ids = []
        for name, score in tags_to_add:
            # Check if exists
            stmt = select(StockTagInfo).where(StockTagInfo.name == name)
            res = await session.execute(stmt)
            tag_info = res.scalar_one_or_none()
            
            if not tag_info:
                continue
            
            tag_ids.append(tag_info.id)
            
        # Optimize: Diff-based update to reduce locking
        # 1. Get existing tags for this stock (calculation type)
        subq_ids = select(StockTagInfo.id).where(StockTagInfo.tag_type == "calculation")
        stmt_exist = select(StockTagRelation.tag_id).where(
            and_(
                StockTagRelation.stock_code == code,
                StockTagRelation.tag_id.in_(subq_ids)
            )
        )
        res_exist = await session.execute(stmt_exist)
        existing_tag_ids = set(res_exist.scalars().all())
        new_tag_ids = set(tag_ids)
        
        to_delete = existing_tag_ids - new_tag_ids
        to_add = new_tag_ids - existing_tag_ids
        
        if to_delete:
            stmt = delete(StockTagRelation).where(
                and_(
                    StockTagRelation.stock_code == code,
                    StockTagRelation.tag_id.in_(to_delete)
                )
            )
            await session.execute(stmt)
            
        if to_add:
            for tid in to_add:
                rel = StockTagRelation(stock_code=code, tag_id=tid)
                session.add(rel)

    @staticmethod
    async def analyze_all_stocks(batch_size: int = 5):
        """
        批量分析所有活跃股票的成交量异动 (并发执行，每批batch_size个)
        """
        logger.info(f"开始执行全量股票成交量异动分析 (Batch Size: {batch_size})...")
        start_time = datetime.now()
        
        session = db_manager.session_factory()
        try:
            # 1. 获取所有活跃股票代码
            stmt = select(StockInfo.code).where(StockInfo.is_active == True)
            result = await session.execute(stmt)
            codes = result.scalars().all()
            
            logger.info(f"共找到 {len(codes)} 只活跃股票，准备分析...")
            
            # 2. 分批并发处理
            total = len(codes)
            processed = 0
            
            for i in range(0, total, batch_size):
                batch_codes = codes[i:i+batch_size]
                
                # 并发执行当前批次
                tasks = []
                for code in batch_codes:
                    # 使用封装函数确保单个失败不影响整体
                    tasks.append(VolumeAnalysisService._safe_analyze_stock(code))
                
                # 等待当前批次所有任务完成 (无论成功失败)
                await asyncio.gather(*tasks)
                
                processed += len(batch_codes)
                logger.info(f"进度: {processed}/{total} ({(processed/total*100):.1f}%)")
                
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"全量异动分析完成，耗时: {duration:.2f}秒")
            
        except Exception as e:
            logger.error(f"全量异动分析任务失败: {e}")
        finally:
            await session.close()

    @staticmethod
    async def _safe_analyze_stock(code: str):
        """
        安全执行单个股票分析，捕获异常
        """
        try:
            # 不传递session，让analyze_stock内部管理独立事务
            await VolumeAnalysisService.analyze_stock(code)
        except Exception as e:
            logger.error(f"分析股票 {code} 失败: {e}")

    @staticmethod
    async def analyze_stock(code: str, session: AsyncSession = None, is_realtime: bool = False):
        """
        全流程分析：使用Pathway引擎 -> 更新旧表（含重试）
        """
        # If external session provided, just run logic
        if session:
            return await VolumeAnalysisService._analyze_stock_impl(code, session)

        # Phase 2: Persistence (Write / Short Transaction)
        # This is where retries happen for deadlocks.
        retries = 3
        last_error = None
        
        for attempt in range(retries):
            write_session = db_manager.session_factory()
            try:
                result = await VolumeAnalysisService._analyze_stock_impl(code, write_session)
                await write_session.commit()
                return result
            except Exception as e:
                await write_session.rollback()
                last_error = e
                # Only retry on Deadlock (1213) or Lock Wait Timeout (1205)
                is_deadlock = "1213" in str(e)
                is_lock_timeout = "1205" in str(e)
                
                if is_deadlock or is_lock_timeout:
                    wait_time = (attempt + 1) * 0.5 # 0.5s, 1.0s, 1.5s
                    logger.warning(f"Deadlock/Lock detected for {code} (Attempt {attempt+1}/{retries}). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # Non-retryable error
                    logger.error(f"Save failed for {code} with non-retryable error: {e}")
                    raise e
            finally:
                await write_session.close()
                
        # If we exhausted retries
        logger.error(f"Failed to save {code} after {retries} attempts. Last error: {last_error}")
        raise last_error

    @staticmethod
    async def _analyze_stock_impl(code: str, session: AsyncSession) -> Dict[str, Any]:
        """
        使用Pathway向量化引擎执行分析
        """
        if "." in code:
            code = code.split(".")[0]

        # 0. 获取股票信息以确定pool_type
        stmt_info = select(StockInfo).where(StockInfo.code == code)
        result_info = await session.execute(stmt_info)
        stock_info = result_info.scalars().first()
        pool_type = 'all'
        if stock_info:
             if stock_info.source == 'wencai':
                 pool_type = 'wencai'
            
        # 1. 获取历史数据（最近400天）
        stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(400)
        result = await session.execute(stmt)
        daily_data = result.scalars().all()
        
        if not daily_data or len(daily_data) < 2:
            logger.warning(f"股票 {code} 数据不足，跳过分析")
            return {}
        
        # 2. 转换为DataFrame
        import pandas as pd
        df = pd.DataFrame([{
            'trade_date': d.trade_date,
            'open': float(d.open) if d.open else 0,
            'close': float(d.close) if d.close else 0,
            'high': float(d.high) if d.high else 0,
            'low': float(d.low) if d.low else 0,
            'vol': float(d.vol) if d.vol else 0
        } for d in daily_data])
        
        # 3. 使用向量化引擎批量计算
        from app.services.pathway_vectorized_engine import PathwayVectorizedEngine
        vectorized_engine = PathwayVectorizedEngine(session)
        await vectorized_engine._ensure_tag_scores()
        
        result_df = vectorized_engine.calculate_batch(df)
        
        # 4. 保存结果到数据库
        await VolumeAnalysisService._save_vectorized_results(code, result_df, session, pool_type=pool_type)
        
        # 5. 更新baseline
        await VolumeAnalysisService._update_baseline_from_vectorized(code, result_df, session)
        
        # 6. 聚合总分
        latest = result_df.iloc[-1]
        total_score = float(latest['total_score']) if 'total_score' in latest else 0
        
        # 7. 更新stock_info
        stmt_info = select(StockInfo).where(StockInfo.code == code)
        res_info = await session.execute(stmt_info)
        info = res_info.scalar_one_or_none()
        
        if info:
            info.volume_anomaly_score = int(total_score)
            info.score_update_time = datetime.now()
        else:
            # 创建新记录
            new_info = StockInfo(
                code=code,
                name=f'股票{code}',
                volume_anomaly_score=int(total_score),
                score_update_time=datetime.now()
            )
            session.add(new_info)
        
        # 8. 返回结果
        return {
            'code': code,
            'total_score': total_score,
            'daily_score': float(latest['daily_score']) if 'daily_score' in latest else 0,
            'tags': latest['tags_str'].split(',') if 'tags_str' in latest else [],
            'trade_date': latest['trade_date']
        }
    
    @staticmethod
    async def calculate_historical_baseline(code: str, end_date: date, session: AsyncSession) -> Decimal:
        """
        计算历史基础分（基于StockDaily数据实时计算过去250天的得分总和）
        用于首次上榜或数据缺失时的自愈
        """
        from app.services.pathway_vectorized_engine import PathwayVectorizedEngine
        import pandas as pd
        
        # 1. 获取过去250天的数据
        start_date = end_date - timedelta(days=VolumeAnalysisService.SCORE_WINDOW_DAYS)
        stmt = select(StockDaily).where(
            StockDaily.code == code,
            StockDaily.trade_date >= start_date,
            StockDaily.trade_date < end_date
        ).order_by(StockDaily.trade_date.asc())
        
        result = await session.execute(stmt)
        daily_data = result.scalars().all()
        
        if not daily_data:
            return Decimal(0)
            
        # 2. 转换为DataFrame
        df = pd.DataFrame([{
            'trade_date': d.trade_date,
            'open': float(d.open) if d.open else 0,
            'close': float(d.close) if d.close else 0,
            'high': float(d.high) if d.high else 0,
            'low': float(d.low) if d.low else 0,
            'vol': float(d.vol) if d.vol else 0
        } for d in daily_data])
        
        if df.empty:
            return Decimal(0)
            
        # 3. 使用向量化引擎计算
        vectorized_engine = PathwayVectorizedEngine(session)
        # 确保标签分数已加载
        await vectorized_engine._ensure_tag_scores()
        
        result_df = vectorized_engine.calculate_batch(df)
        
        # 4. 汇总得分
        total_baseline = Decimal(0)
        if 'daily_score' in result_df.columns:
            total_baseline = Decimal(str(result_df['daily_score'].sum()))
            
        return total_baseline

    @staticmethod
    async def _save_vectorized_results(code: str, result_df, session: AsyncSession, pool_type: str = 'all'):
        """
        保存向量化计算结果到数据库
        
        Args:
            code: 股票代码
            result_df: 向量化计算结果DataFrame
            session: 数据库会话
            pool_type: 股票池类型
        """
        from app.models.stock_daily import StockScoreResult
        
        for _, row in result_df.iterrows():
            # 解析tags_str
            tags_str = row.get('tags_str', '')
            tags = tags_str.split(',') if tags_str else []
            
            # 构建rule_scores
            rule_scores = {}
            for tag in tags:
                if tag and tag != 'basic_info':
                    rule_scores[tag] = VolumeAnalysisService.TAG_SCORES.get(tag, 0)
            
            # 检查是否已存在
            stmt = select(StockScoreResult).where(
                StockScoreResult.code == code,
                StockScoreResult.trade_date == row['trade_date']
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            # Calculate accumulated score
            # Note: This simple loop assumes result_df is sorted by date and we process continuously.
            # However, for a robust batch update, we should really fetch the previous accumulated score 
            # from DB if this is the first item, or track it.
            # But _save_vectorized_results is often called with a batch.
            # To do this correctly without fetching for every row:
            # We need to know the accumulated score BEFORE this batch.
            
            # Since this function iterates, let's assume the caller or a separate logic handles strict accumulation 
            # OR we implement a "running total" here if the batch is contiguous.
            # For now, let's just save daily_score. The accumulation logic is strictly enforced in RuleEngineService 
            # and _calculate_stock_internal. 
            # If we want to support it here, we need to fetch the previous day's accumulated score.
            
            # Let's try to fetch previous accumulated score if we don't have it in the batch context
            # But doing it inside the loop is slow.
            # Ideally, result_df should have 'accumulated_score' calculated if possible.
            # If not, we just save daily_score and total_score (as daily) for now, 
            # BUT the user wants strict separation.
            
            # Strategy: 
            # 1. Fetch prev_accumulated before loop.
            # 2. Update continuously.
            
            daily_score = Decimal(str(row.get('daily_score', 0)))
            
            if existing:
                # 更新
                existing.daily_score = daily_score
                existing.rule_scores = rule_scores
                existing.updated_at = datetime.now()
                # We don't update accumulated_score here to avoid breaking chain if we are just patching daily scores
                # UNLESS we are sure we are recalculating everything.
                # For safety, let's leave accumulated_score alone if it exists, or set it to daily_score if 0?
                # No, that breaks logic. 
                # Better approach: Just save daily_score. The user can run a "recalculate accumulation" script.
                # OR: We implement proper accumulation here.
                
                # If we are in "recalculate" mode (often implied by using vectorized engine), we might want to reset.
                pass 
                
                # 如果是明确的pool_type，也更新它
                if pool_type != 'all' and existing.pool_type == 'all':
                     existing.pool_type = pool_type
            else:
                # 插入
                # For new records, we MUST calculate accumulated score if we want consistency.
                # But querying every time is slow.
                # Let's just save daily_score. RuleEngineService will handle the daily incremental updates.
                # This function is used for "historical baseline" often.
                
                score_result = StockScoreResult(
                    code=code,
                    trade_date=row['trade_date'],
                    rule_scores=rule_scores,
                    daily_score=daily_score,
                    total_score=daily_score, # Temporary fallback
                    accumulated_score=daily_score, # Temporary fallback (will be fixed by recalc)
                    pool_type=pool_type
                )
                session.add(score_result)
        
        await session.commit()
        logger.debug(f"💾 已保存 {len(result_df)} 条评分结果")
    
    @staticmethod
    async def _update_baseline_from_vectorized(code: str, result_df, session: AsyncSession):
        """
        从向量化结果更新baseline（带Redis缓存失效）
        
        Args:
            code: 股票代码
            result_df: 向量化计算结果DataFrame
            session: 数据库会话
        """
        from app.services.redis_cache_service import redis_cache_service
        from app.models.volume_analysis import StockVolumeBaseline
        
        # 获取最新数据
        latest = result_df.iloc[-1]
        
        # 查找最近的3倍量和2倍量
        vol_3x_rows = result_df[result_df['tags_str'].str.contains('3倍量', na=False)]
        vol_2x_rows = result_df[result_df['tags_str'].str.contains('2倍量', na=False)]
        
        # 获取最近的3倍量
        if not vol_3x_rows.empty:
            last_3x = vol_3x_rows.iloc[-1]
            last_3x_date = last_3x['trade_date']
            last_3x_close = last_3x['close']
        else:
            last_3x_date = None
            last_3x_close = None
        
        # 获取最近的2倍量
        if not vol_2x_rows.empty:
            last_2x = vol_2x_rows.iloc[-1]
            last_2x_date = last_2x['trade_date']
            last_2x_close = last_2x['close']
        else:
            last_2x_date = None
            last_2x_close = None
        
        # 查找最近的地量
        vol_60d_rows = result_df[result_df['tags_str'].str.contains('60日地量', na=False)]
        vol_30d_rows = result_df[result_df['tags_str'].str.contains('30日地量', na=False)]
        vol_20d_rows = result_df[result_df['tags_str'].str.contains('20日地量', na=False)]
        vol_10d_rows = result_df[result_df['tags_str'].str.contains('10日地量', na=False)]
        vol_5d_rows = result_df[result_df['tags_str'].str.contains('5日地量', na=False)]
        
        # 获取最近的地量
        def get_latest_vol(rows):
            if rows.empty:
                return None, None
            latest = rows.iloc[-1]
            return latest['trade_date'], latest['vol']
        
        last_60d_date, last_60d_vol = get_latest_vol(vol_60d_rows)
        last_30d_date, last_30d_vol = get_latest_vol(vol_30d_rows)
        last_20d_date, last_20d_vol = get_latest_vol(vol_20d_rows)
        last_10d_date, last_10d_vol = get_latest_vol(vol_10d_rows)
        last_5d_date, last_5d_vol = get_latest_vol(vol_5d_rows)
        
        # 更新或创建baseline
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        result = await session.execute(stmt)
        baseline = result.scalar_one_or_none()
        
        if baseline:
            # 更新
            baseline.last_3x_date = last_3x_date
            baseline.last_3x_close = last_3x_close
            baseline.last_2x_date = last_2x_date
            baseline.last_2x_close = last_2x_close
            baseline.last_5d_low_vol_date = last_5d_date
            baseline.last_5d_low_vol = last_5d_vol
            baseline.last_10d_low_vol_date = last_10d_date
            baseline.last_10d_low_vol = last_10d_vol
            baseline.last_20d_low_vol_date = last_20d_date
            baseline.last_20d_low_vol = last_20d_vol
            baseline.last_30d_low_vol_date = last_30d_date
            baseline.last_30d_low_vol = last_30d_vol
            baseline.last_60d_low_vol_date = last_60d_date
            baseline.last_60d_low_vol = last_60d_vol
            baseline.updated_at = datetime.now()
        else:
            # 创建
            baseline = StockVolumeBaseline(
                code=code,
                last_3x_date=last_3x_date,
                last_3x_close=last_3x_close,
                last_2x_date=last_2x_date,
                last_2x_close=last_2x_close,
                last_5d_low_vol_date=last_5d_date,
                last_5d_low_vol=last_5d_vol,
                last_10d_low_vol_date=last_10d_date,
                last_10d_low_vol=last_10d_vol,
                last_20d_low_vol_date=last_20d_date,
                last_20d_low_vol=last_20d_vol,
                last_30d_low_vol_date=last_30d_date,
                last_30d_low_vol=last_30d_vol,
                last_60d_low_vol_date=last_60d_date,
                last_60d_low_vol=last_60d_vol
            )
            session.add(baseline)
        
        await session.commit()
        
        # 删除Redis缓存，强制下次从数据库读取
        redis_cache_service.delete_baseline(code)
        
        logger.debug(f"💾 已更新baseline: {code}")
  
    @staticmethod
    async def _update_legacy_tables(session: AsyncSession, code: str, stock_daily: StockDaily, pathway_result: Dict):
        """
        更新旧表数据 (StockVolumeBaseline, VolumeAnalysisResult)
        """
        tags = pathway_result.get('tags', [])
        trade_date = stock_daily.trade_date
        
        # --- Update VolumeAnalysisResult ---
        # Only if we want to track anomalies in the old table
        for tag in tags:
            name = tag['name']
            value = tag['value']
            score = tag.get('score', 0)
            
            # Map tag name to analysis_type or similar
            # Existing types: '3倍量', '60日地量' etc.
            if name in VolumeAnalysisService.TAG_SCORES:
                # Check if already exists
                stmt = select(VolumeAnalysisResult).where(
                    VolumeAnalysisResult.code == code,
                    VolumeAnalysisResult.trade_date == trade_date,
                    VolumeAnalysisResult.analysis_type == name
                )
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()
                
                if not existing:
                    entry = VolumeAnalysisResult(
                        code=code,
                        trade_date=trade_date,
                        analysis_type=name,
                        value=value,
                        description=f"Pathway: {name}",
                        extra_data={"score": score}
                    )
                    session.add(entry)

        # --- Update StockVolumeBaseline ---
        # 1. Get or Create Baseline
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        res = await session.execute(stmt)
        baseline = res.scalar_one_or_none()
        
        if not baseline:
            baseline = StockVolumeBaseline(code=code)
            session.add(baseline)
        
        # 2. Update fields based on tags
        for tag in tags:
            name = tag['name']
            value = float(tag['value'])
            
            if name == '3倍量':
                baseline.last_3x_date = trade_date
                baseline.last_3x_close = stock_daily.close
            elif name == '2倍量':
                baseline.last_2x_date = trade_date
                baseline.last_2x_close = stock_daily.close
            elif name == '5日地量':
                baseline.last_5d_low_vol_date = trade_date
                baseline.last_5d_low_vol = stock_daily.vol
            elif name == '10日地量':
                baseline.last_10d_low_vol_date = trade_date
                baseline.last_10d_low_vol = stock_daily.vol
            elif name == '20日地量':
                baseline.last_20d_low_vol_date = trade_date
                baseline.last_20d_low_vol = stock_daily.vol
            elif name == '30日地量':
                baseline.last_30d_low_vol_date = trade_date
                baseline.last_30d_low_vol = stock_daily.vol
            elif name == '60日地量':
                baseline.last_60d_low_vol_date = trade_date
                baseline.last_60d_low_vol = stock_daily.vol

    @staticmethod
    async def _calculate_stock_internal(code: str, session: AsyncSession, is_realtime: bool = False) -> Dict[str, Any]:
        """
        只负责计算，不进行任何写操作
        """
        logger.info(f"Start calculating stock: {code}")
            
        try:
            # 0. 获取股票信息以确定pool_type
            stmt_info = select(StockInfo).where(StockInfo.code == code)
            result_info = await session.execute(stmt_info)
            stock_info = result_info.scalars().first()
            pool_type = 'all'
            if stock_info:
                 if stock_info.source == 'wencai':
                     pool_type = 'wencai'

            if "." in code:
                code = code.split(".")[0]
            
            # 1. Fetch Daily Data
            stmt = select(StockDaily).where(StockDaily.code == code).order_by(StockDaily.trade_date.desc()).limit(400)
            result = await session.execute(stmt)
            daily_data = result.scalars().all()
            
            if len(daily_data) < 2:
                logger.warning(f"Insufficient data for {code}: {len(daily_data)} records")
                return {"should_skip": True}
            
            daily_data = sorted(daily_data, key=lambda x: x.trade_date)
            
            # --- Date Check Logic ---
            today = datetime.now().date()
            csv_latest_date = daily_data[-1].trade_date if daily_data else None
            
            stmt = select(func.max(StockScoreResult.trade_date)).where(StockScoreResult.code == code)
            last_scored_date = await session.scalar(stmt)
            
            # logger.info(f"Date Check [{code}]: Today={today}, CSV_Latest={csv_latest_date}, Last_Score={last_scored_date}")
            
            if not is_realtime:
                should_skip = False
                skip_reason = ""
                
                if last_scored_date:
                    if csv_latest_date and last_scored_date >= csv_latest_date:
                        should_skip = True
                        skip_reason = f"Score Date ({last_scored_date}) >= CSV Date ({csv_latest_date})"
                    elif last_scored_date >= today:
                        should_skip = True
                        skip_reason = f"Score Date ({last_scored_date}) >= Today ({today})"
                
                if should_skip:
                    logger.info(f"Skipping {code}: {skip_reason}")
                    baseline = await VolumeAnalysisService.get_baseline(code, session)
                    stmt_info = select(StockInfo).where(StockInfo.code == code)
                    res_info = await session.execute(stmt_info)
                    info = res_info.scalars().first()
                    if info and info.volume_anomaly_score is not None:
                        baseline['anomaly_score'] = info.volume_anomaly_score
                    else:
                        baseline['anomaly_score'] = 0
                    return {"should_skip": True, "baseline": baseline}
            
            # --- Load Score Configuration ---
            stmt = select(StockTagInfo).where(StockTagInfo.tag_type == 'calculation')
            result = await session.execute(stmt)
            calc_tags = result.scalars().all()
            score_config = {tag.name: float(tag.score) for tag in calc_tags}
            
            def get_score(name, default=0):
                return score_config.get(name, default)
                
            # --- Pre-calculation (Breakout) ---
            last_3x_close = None
            last_3x_date = None
            last_2x_close = None
            last_2x_date = None
            
            for k in range(len(daily_data) - 2, -1, -1):
                d = daily_data[k]
                prev_d = daily_data[k-1] if k > 0 else None
                if not prev_d or not prev_d.vol or prev_d.vol == 0: continue
                ratio = float(d.vol or 0) / float(prev_d.vol)
                if not last_3x_close and ratio >= 3:
                    last_3x_close = float(d.close)
                    last_3x_date = d.trade_date
                if not last_2x_close and ratio >= 2:
                    last_2x_close = float(d.close)
                    last_2x_date = d.trade_date
                if last_3x_close and last_2x_close:
                    break
            
            # Collectors
            latest_3x_record = None 
            latest_2x_record = None
            latest_low_vol_records = {} 
            anomalies = []
            daily_scores = []
            logs = []
            alerts = []
            
            # Iterate
            for i in range(1, len(daily_data)):
                current = daily_data[i]
                prev = daily_data[i-1]
                is_latest_point = (i == len(daily_data) - 1)
                
                if not is_realtime and last_scored_date and current.trade_date <= last_scored_date:
                    continue

                if not current or not prev: continue
                cur_vol = float(current.vol or 0)
                prev_vol = float(prev.vol or 0)
                if prev_vol <= 0 or cur_vol <= 0: continue
                
                vol_ratio = cur_vol / prev_vol
                close_price = current.close
                if close_price is None: continue
                
                tag = "[实时数据]" if (is_realtime and is_latest_point) else "[历史数据]"
                day_score = 0
                day_rule_scores = {}

                if is_latest_point:
                     logs.append({
                        "code": code,
                        "rule_name": "规则检查",
                        "is_match": False,
                        "details": f"{tag} 开始执行规则检查: 1.地量检查 2.价格突破检查 3.量比检查"
                     })

                # 1. Low Volume
                def check_low_volume(days):
                    if i < days: return None
                    min_past_vol = float('inf')
                    min_past_date = None
                    valid_data_count = 0
                    for k in range(1, days): 
                        past_data = daily_data[i-k]
                        past_vol = float(past_data.vol or 0)
                        if past_vol <= 0: continue
                        valid_data_count += 1
                        if past_vol < min_past_vol:
                            min_past_vol = past_vol
                            min_past_date = past_data.trade_date
                    if valid_data_count == 0: return None
                    if cur_vol < min_past_vol:
                        return (min_past_vol, min_past_date)
                    return None
                
                low_vol_triggered = False
                longest_period_found = None
                
                for days in [60, 30, 20, 10, 5]:
                    result = check_low_volume(days)
                    if result:
                        latest_low_vol_records[str(days)] = {"date": current.trade_date, "vol": float(cur_vol)}
                        prev_min_vol, prev_min_date = result
                        anomalies.append(VolumeAnalysisService._create_low_vol_entry(code, current, days))
                        
                        pts = get_score(f"{days}日地量", 0)
                        if pts > 0:
                            day_score += pts
                            day_rule_scores[f'{days}日地量'] = pts
                        
                        if longest_period_found is None:
                            longest_period_found = days
                            low_vol_triggered = True
                        
                        if is_latest_point:
                            log_msg = f"[{current.trade_date}] 当前量:{cur_vol}手 创{days}日（{prev_min_date}）新低（{prev_min_vol}手）"
                            logs.append({
                                "code": code,
                                "rule_name": f"{days}日地量",
                                "is_match": True,
                                "details": log_msg
                            })
                            alerts.append({
                                "code": code,
                                "alert_type": f"Volume_Low_{days}d",
                                "message": f"{tag} 触发{days}日地量: {log_msg}",
                                "is_sent": False
                            })
                
                if not low_vol_triggered and is_latest_point:
                     logs.append({
                        "code": code,
                        "rule_name": "地量检查",
                        "is_match": False,
                        "details": f"{tag} 未触发地量 (5/10/20/30/60日)"
                     })

                # 2. Price Breakout
                if is_latest_point and last_3x_close and last_2x_close:
                    if float(close_price) > last_3x_close and float(close_price) > last_2x_close:
                        pts = get_score("价格双重突破", 0)
                        day_score += pts
                        day_rule_scores['价格双重突破'] = pts
                        cur_time_str = datetime.now().strftime("%Y-%m-%d %H:%M") if is_realtime else str(current.trade_date)
                        breakout_msg = (f"{tag} 当前（{cur_time_str}） 价格({close_price}) "
                                        f"同时突破最近（{last_3x_date}）3倍量收盘价({last_3x_close})和"
                                        f"最近（{last_2x_date}）2倍量收盘价({last_2x_close})")
                        logs.append({
                            "code": code,
                            "rule_name": "价格双重突破",
                            "is_match": True,
                            "details": breakout_msg
                        })
                        alerts.append({
                            "code": code,
                            "alert_type": "Price_Breakout",
                            "message": breakout_msg,
                            "is_sent": False
                        })
                    else:
                        logs.append({
                            "code": code,
                            "rule_name": "价格双重突破",
                            "is_match": False,
                            "details": f"{tag} 未突破: 当前{close_price} vs 3倍量{last_3x_close}/2倍量{last_2x_close}"
                        })
                elif is_latest_point:
                     logs.append({
                            "code": code,
                            "rule_name": "价格双重突破",
                            "is_match": False,
                            "details": f"{tag} 无法检查: 缺少历史3倍/2倍量数据"
                        })
                
                # 3. Volume Multiplier
                if vol_ratio >= 3:
                    pts = get_score("3倍量", 0)
                    day_score += pts
                    day_rule_scores['3倍量'] = pts
                    desc = f"{tag} 成交量是昨天的{vol_ratio:.2f}倍"
                    anomalies.append({
                        "code": code,
                        "trade_date": current.trade_date,
                        "analysis_type": "3倍量",
                        "value": close_price,
                        "description": desc,
                        "extra_data": {"vol_ratio": vol_ratio, "vol": cur_vol, "is_realtime": is_realtime and is_latest_point}
                    })
                    latest_3x_record = {"date": current.trade_date, "close": float(close_price)}
                    if is_latest_point:
                        logs.append({
                            "code": code,
                            "rule_name": "3倍量",
                            "is_match": True,
                            "details": f"[{current.trade_date}] 当前量:{cur_vol}手, 昨日量:{prev_vol}手, 倍数:{vol_ratio:.2f}"
                        })
                        alerts.append({
                            "code": code,
                            "alert_type": "Volume_3x",
                            "message": f"{tag} 触发3倍量异动: {desc}",
                            "is_sent": False
                        })
                elif vol_ratio >= 2:
                    pts = get_score("2倍量", 0)
                    day_score += pts
                    day_rule_scores['2倍量'] = pts
                    desc = f"{tag} 成交量是昨天的{vol_ratio:.2f}倍"
                    anomalies.append({
                        "code": code,
                        "trade_date": current.trade_date,
                        "analysis_type": "2倍量",
                        "value": close_price,
                        "description": desc,
                        "extra_data": {"vol_ratio": vol_ratio, "vol": cur_vol, "is_realtime": is_realtime and is_latest_point}
                    })
                    latest_2x_record = {"date": current.trade_date, "close": float(close_price)}
                    if is_latest_point:
                        logs.append({
                            "code": code,
                            "rule_name": "2倍量",
                            "is_match": True,
                            "details": f"[{current.trade_date}] 当前量:{cur_vol}手, 昨日量:{prev_vol}手, 倍数:{vol_ratio:.2f}"
                        })

                if day_score > 0:
                        daily_scores.append({
                            'code': code,
                            'trade_date': current.trade_date,
                            'total_score': day_score,
                            'rule_scores': day_rule_scores,
                            'pool_type': pool_type
                        })

            return {
                "should_skip": False,
                "daily_scores": daily_scores,
                "anomalies": anomalies,
                "logs": logs,
                "alerts": alerts,
                "baseline_update": {
                    "latest_3x_record": latest_3x_record,
                    "latest_2x_record": latest_2x_record,
                    "latest_low_vol_records": latest_low_vol_records
                },
                "latest_price": daily_data[-1].close if daily_data else None,
                "latest_date": daily_data[-1].trade_date if daily_data else None
            }

        except Exception as e:
            logger.error(f"Error calculating {code}: {e}")
            raise e

    @staticmethod
    async def _save_stock_internal(code: str, data: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
        """
        负责将计算结果写入数据库 (Short Transaction)
        """
        daily_scores = data.get("daily_scores", [])
        anomalies = data.get("anomalies", [])
        logs = data.get("logs", [])
        alerts = data.get("alerts", [])
        baseline_update = data.get("baseline_update", {})
        
        # 1. Bulk Upsert Scores
        if daily_scores:
            stmt = mysql_insert(StockScoreResult).values(daily_scores)
            update_dict = {
                "total_score": stmt.inserted.total_score,
                "rule_scores": stmt.inserted.rule_scores,
                "pool_type": stmt.inserted.pool_type
            }
            on_duplicate_key_stmt = stmt.on_duplicate_key_update(**update_dict)
            await session.execute(on_duplicate_key_stmt)

        # 2. Bulk Upsert Anomalies (Using Unique Constraint)
        if anomalies:
            # We use INSERT ... ON DUPLICATE KEY UPDATE to avoid deadlocks caused by DELETE+INSERT
            stmt = mysql_insert(VolumeAnalysisResult).values(anomalies)
            
            # If duplicate, we can update specific fields or just do nothing if data is identical.
            # Here we update value/description to be safe.
            update_dict = {
                "value": stmt.inserted.value,
                "description": stmt.inserted.description,
                "extra_data": stmt.inserted.extra_data
            }
            on_duplicate_key_stmt = stmt.on_duplicate_key_update(**update_dict)
            await session.execute(on_duplicate_key_stmt)

        # 3. Logs and Alerts (Append Only)
        if logs:
            session.add_all([RuleCalculationLog(**log) for log in logs])
        if alerts:
            session.add_all([AlertRecord(**alert) for alert in alerts])
            
        # 4. Update Baseline
        baseline = await VolumeAnalysisService.get_baseline(code, session)
        if baseline_update.get("latest_3x_record"):
            baseline['latest_3x_record'] = baseline_update['latest_3x_record']
        if baseline_update.get("latest_2x_record"):
            baseline['latest_2x_record'] = baseline_update['latest_2x_record']
        if baseline_update.get("latest_low_vol_records"):
            # Merge dictionary
            if not baseline.get('latest_low_vol_records'):
                baseline['latest_low_vol_records'] = {}
            baseline['latest_low_vol_records'].update(baseline_update['latest_low_vol_records'])
            
        await VolumeAnalysisService.save_baseline(code, baseline, session)
        
        # 5. Calculate and Update Total Score in StockInfo
        # We need to query DB for the total score over last SCORE_WINDOW_DAYS days
        cutoff_date = datetime.now().date() - timedelta(days=VolumeAnalysisService.SCORE_WINDOW_DAYS)
        stmt_score = select(func.sum(StockScoreResult.total_score)).where(
            StockScoreResult.code == code,
            StockScoreResult.trade_date >= cutoff_date
        )
        total_score = await session.scalar(stmt_score) or 0
        
        # Update StockInfo
        # Generate bonus items string from the LATEST day's anomalies
        latest_date = data.get("latest_date")
        bonus_items_list = []
        if latest_date:
            todays_anomalies = [a for a in anomalies if a['trade_date'] == latest_date]
            for a in todays_anomalies:
                bonus_items_list.append(f"{a['analysis_type']}")
        
        bonus_items_json = json.dumps(bonus_items_list, ensure_ascii=False) if bonus_items_list else None
        
        stmt_update = update(StockInfo).where(StockInfo.code == code).values(
            volume_anomaly_score=total_score,
            updated_at=datetime.now(),
            bonus_items=bonus_items_json
        )
        if data.get("latest_price"):
             stmt_update = stmt_update.values(latest_price=data.get("latest_price"))
             
        await session.execute(stmt_update)
        
        baseline['anomaly_score'] = total_score
        return baseline

    @staticmethod
    def _create_low_vol_entry(code, current, days):
        return {
            "code": code,
            "trade_date": current.trade_date,
            "analysis_type": f"{days}日地量",
            "value": current.vol, # Volume for low vol
            "description": f"{days}日内地量",
            "extra_data": {"vol": float(current.vol)}
        }

    @staticmethod
    async def get_baseline(code: str, session: AsyncSession) -> Dict[str, Any]:
        """
        获取最新的基准数据（带Redis缓存）
        
        Args:
            code: 股票代码
            session: 数据库会话
        
        Returns:
            baseline数据字典
        """
        from app.services.redis_cache_service import redis_cache_service
        
        # 1. 尝试从Redis缓存读取
        cached_baseline = redis_cache_service.get_baseline(code)
        if cached_baseline:
            return cached_baseline
        
        # 2. 从数据库读取
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        result = await session.execute(stmt)
        record = result.scalars().first()
        
        baseline = {}
        if record:
            if record.last_3x_date:
                baseline['last_3x_close'] = {
                    "date": record.last_3x_date,
                    "value": float(record.last_3x_close) if record.last_3x_close else 0.0
                }
            if record.last_2x_date:
                baseline['last_2x_close'] = {
                    "date": record.last_2x_date,
                    "value": float(record.last_2x_close) if record.last_2x_close else 0.0
                }
            
            for days in [5, 10, 20, 30, 60]:
                date_val = getattr(record, f"last_{days}d_low_vol_date")
                vol_val = getattr(record, f"last_{days}d_low_vol")
                
                if date_val:
                    key = f"last_{days}d_low_vol"
                    baseline[key] = {
                        "date": date_val,
                        "value": float(vol_val) if vol_val else 0.0
                    }
        
        # 3. 写入Redis缓存（过期时间：1小时）
        if baseline:
            redis_cache_service.set_baseline(code, baseline, expire_seconds=3600)
        
        return baseline

    @staticmethod
    async def save_baseline(code: str, baseline_data: Dict[str, Any], session: AsyncSession):
        """
        保存基准数据 (StockVolumeBaseline)
        
        基准量计算规则:
        1. 3倍量/2倍量: 记录最近一次发生3倍/2倍量的日期和收盘价。
           - 用于判断后续缩量回调的支撑位置。
        2. 地量 (Low Volume): 记录最近一次5/10/20/30/60日地量的日期和成交量。
           - 5日地量: 最近5个交易日成交量最小
           - 60日地量: 最近60个交易日成交量最小 (长期底部信号)
        
        监控报警来源:
        - 每日监控 (MonitorEngine) 会读取此表中的基准数据。
        - 将今日实时成交量/收盘价与基准数据进行对比。
        - 例如: 今日缩量至60日地量水平 -> 触发报警。
        """
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        result = await session.execute(stmt)
        record = result.scalars().first()
        
        if not record:
            record = StockVolumeBaseline(code=code)
            session.add(record)
            
        # Update 3x/2x
        # 规则: 总是更新为最新的日期 (Latest Date)
        if 'latest_3x_record' in baseline_data:
            rec = baseline_data['latest_3x_record']
            if not record.last_3x_date or rec['date'] >= record.last_3x_date:
                record.last_3x_date = rec['date']
                record.last_3x_close = Decimal(str(rec['close']))

        if 'latest_2x_record' in baseline_data:
            rec = baseline_data['latest_2x_record']
            if not record.last_2x_date or rec['date'] >= record.last_2x_date:
                record.last_2x_date = rec['date']
                record.last_2x_close = Decimal(str(rec['close']))
                
        # Update Low Vol
        # 规则: 总是更新为最新的日期
        if 'latest_low_vol_records' in baseline_data:
            for days, data in baseline_data['latest_low_vol_records'].items():
                date_attr = f"last_{days}d_low_vol_date"
                vol_attr = f"last_{days}d_low_vol"
                
                new_date = data["date"]
                new_vol = Decimal(str(data["vol"]))
                
                current_date = getattr(record, date_attr)
                if not current_date or new_date >= current_date:
                    setattr(record, date_attr, new_date)
                    setattr(record, vol_attr, new_vol)

    @staticmethod
    async def log_rule_calculation(code: str, rule_name: str, is_match: bool, details: str, session: AsyncSession = None):
        should_close = False
        if not session:
            session = db_manager.session_factory()
            should_close = True
        try:
            log = RuleCalculationLog(
                code=code,
                rule_name=rule_name,
                is_match=is_match,
                details=details
            )
            session.add(log)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            if should_close:
                await session.close()

    @staticmethod
    async def log_alert(code: str, alert_type: str, message: str, session: AsyncSession = None):
        should_close = False
        if not session:
            session = db_manager.session_factory()
            should_close = True
        try:
            alert = AlertRecord(
                code=code,
                alert_type=alert_type,
                message=message,
                is_sent=False 
            )
            session.add(alert)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            if should_close:
                await session.close()
