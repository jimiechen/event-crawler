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

from loguru import logger

class VolumeAnalysisService:
    
    @staticmethod
    async def generate_daily_tags(code: str, target_date: date, session: AsyncSession):
        """
        生成指定日期股票的标签（基于成交量异动）
        并更新到 stock_tag_relations 表
        """
        # 1. 获取数据 (Target Date + Past 100 days)
        start_date = target_date - timedelta(days=100) 
        stmt = select(StockDaily).where(
            and_(
                StockDaily.code == code,
                StockDaily.trade_date >= start_date,
                StockDaily.trade_date <= target_date
            )
        ).order_by(StockDaily.trade_date.asc())
        
        result = await session.execute(stmt)
        daily_data = result.scalars().all()
        
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
            
        # Delete old relations for "calculation" tags
        subq = select(StockTagInfo.id).where(StockTagInfo.tag_type == "calculation")
        
        stmt = delete(StockTagRelation).where(
            and_(
                StockTagRelation.stock_code == code,
                StockTagRelation.tag_id.in_(subq)
            )
        )
        await session.execute(stmt)
        
        # Insert new
        for tid in tag_ids:
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
        全流程分析：计算 -> 保存（含重试）
        """
        # Phase 1: Calculation (Read-Only / Long Running)
        # We use a dedicated read session if none provided, or use provided one.
        read_session = session or db_manager.session_factory()
        should_close_read = session is None
        
        calc_results = None
        try:
            calc_results = await VolumeAnalysisService._calculate_stock_internal(code, read_session, is_realtime)
        except Exception as e:
            logger.error(f"Calculation failed for {code}: {e}")
            raise e
        finally:
            if should_close_read:
                await read_session.close()

        if not calc_results or calc_results.get("should_skip"):
            return calc_results.get("baseline", {})
            
        # Phase 2: Persistence (Write / Short Transaction)
        # This is where retries happen for deadlocks.
        retries = 3
        last_error = None
        
        for attempt in range(retries):
            # If external session provided, just save and let caller handle commit/rollback
            if session:
                return await VolumeAnalysisService._save_stock_internal(code, calc_results, session)

            write_session = db_manager.session_factory()
            try:
                result = await VolumeAnalysisService._save_stock_internal(code, calc_results, write_session)
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
    async def _calculate_stock_internal(code: str, session: AsyncSession, is_realtime: bool = False) -> Dict[str, Any]:
        """
        只负责计算，不进行任何写操作
        """
        logger.info(f"Start calculating stock: {code}")
            
        try:
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
                        'pool_type': 'unknown'
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
        # We need to query DB for the total score over last 250 days
        cutoff_date = datetime.now().date() - timedelta(days=250)
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
        获取最新的基准数据
        """
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
                    
        return baseline

    @staticmethod
    async def save_baseline(code: str, baseline_data: Dict[str, Any], session: AsyncSession):
        """
        保存基准数据
        """
        stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
        result = await session.execute(stmt)
        record = result.scalars().first()
        
        if not record:
            record = StockVolumeBaseline(code=code)
            session.add(record)
            
        # Update 3x/2x
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
