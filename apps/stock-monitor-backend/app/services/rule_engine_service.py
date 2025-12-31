#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则计算引擎服务
"""

import json
import asyncio
from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
from loguru import logger
from sqlalchemy import select, delete

from app.models.stock_daily import StockScoreResult, StockDaily
from app.models.stock import SystemConfig
from app.models.tag_management import StockTagRelation, StockTagInfo
from app.repositories.stock_daily_repository import StockDailyRepository
from app.database import DatabaseManager
from app.services.volume_analysis_service import VolumeAnalysisService

class RuleEngineService:
    _is_running_historical = False

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repository = StockDailyRepository(db_manager)
        
        # 默认规则配置
        self.default_rules = {
            "vol_2_9": {"name": "2.9倍量", "score": 10, "enabled": True},
            "vol_double": {"name": "倍量", "score": 5, "enabled": True},
            "low_vol_5": {"name": "5天地量", "score": 5, "enabled": True},
            "low_vol_10": {"name": "10天地量", "score": 10, "enabled": True},
            "low_vol_20": {"name": "20天地量", "score": 20, "enabled": True},
            # 标签加分规则
            "tag_3x_vol": {"name": "三倍量标签", "score": 15, "enabled": True},
            "tag_hot": {"name": "近期热点标签", "score": 5, "enabled": True} 
        }

    async def get_rule_config(self) -> Dict[str, Any]:
        """获取规则配置"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == "score_rules")
            )
            config = result.scalar_one_or_none()
            
            if config and config.config_value:
                try:
                    return json.loads(config.config_value)
                except json.JSONDecodeError:
                    pass
            
            return self.default_rules

    async def save_rule_config(self, rules: Dict[str, Any]):
        """保存规则配置"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key == "score_rules")
            )
            config = result.scalar_one_or_none()
            
            if config:
                config.config_value = json.dumps(rules, ensure_ascii=False)
            else:
                config = SystemConfig(
                    config_key="score_rules",
                    config_value=json.dumps(rules, ensure_ascii=False),
                    description="评分规则配置"
                )
                session.add(config)
            await session.commit()

    async def recalculate_historical_scores(self, days: int = 250):
        """
        重新计算过去N天的历史评分 (用于初始化或修正数据)
        """
        if RuleEngineService._is_running_historical:
            logger.warning("Historical calculation is already running. Skipping this request.")
            return {"status": "skipped", "message": "Task already running"}

        RuleEngineService._is_running_historical = True
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            logger.info(f"开始补算历史评分: {start_date} ~ {end_date} ({days}天)")

            # 获取交易日历 (确保只计算交易日)
            async with self.db_manager.get_session() as session:
                # 简单起见，从 stock_daily 表中获取有数据的日期列表
                # 也可以从 tushare 的 trade_cal 获取，但这里直接用现有数据更稳妥
                from sqlalchemy import distinct
                stmt = select(distinct(StockDaily.trade_date))\
                    .where(StockDaily.trade_date.between(start_date, end_date))\
                    .order_by(StockDaily.trade_date.asc())
                result = await session.execute(stmt)
                trade_dates = result.scalars().all()
            
            logger.info(f"共找到 {len(trade_dates)} 个交易日需要计算")
            
            for idx, target_date in enumerate(trade_dates):
                logger.info(f"[{idx+1}/{len(trade_dates)}] 正在计算 {target_date} 的评分...")
                await self.calculate_daily_scores(target_date=target_date)
                
            logger.info("历史评分补算任务完成")
            return {"status": "success", "processed_days": len(trade_dates)}
        except Exception as e:
            logger.error(f"历史评分补算任务异常: {e}")
            raise
        finally:
            RuleEngineService._is_running_historical = False

    async def _get_stock_tags(self, codes: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """获取股票关联的标签列表"""
        async with self.db_manager.get_session() as session:
            stmt = select(StockTagRelation.stock_code, StockTagInfo.name, StockTagInfo.score)\
                .join(StockTagInfo, StockTagRelation.tag_id == StockTagInfo.id)\
                .where(
                    StockTagRelation.stock_code.in_(codes),
                    StockTagInfo.is_deleted == False
                )
            result = await session.execute(stmt)
            
            tag_map = {}
            for code, tag_name, tag_score in result.all():
                if code not in tag_map:
                    tag_map[code] = []
                tag_map[code].append({"name": tag_name, "score": float(tag_score)})
            return tag_map

    async def calculate_daily_scores(self, target_date: Optional[date] = None, force: bool = False, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """
        计算每日评分
        :param target_date: 目标日期，默认为最近的有数据的交易日
        :param force: 是否强制重新计算(忽略已存在的评分)
        :param stock_code: 指定单只股票代码，如果提供则只计算该股票
        """
        if not target_date:
            # 自动获取最近的有数据的日期
            async with self.db_manager.get_session() as session:
                 from sqlalchemy import func
                 result = await session.execute(select(func.max(StockDaily.trade_date)))
                 target_date = result.scalar()
            
            if not target_date:
                target_date = date.today()

        start_time = datetime.now()
        logger.info(f"开始计算 {target_date} 的评分")
        
        try:
            # 1. 获取规则配置
            rules = await self.get_rule_config()
            
            # 2. 获取目标股票列表
            if stock_code:
                target_codes = [stock_code]
            else:
                target_codes = await self.repository.get_target_stocks()
            
            if not target_codes:
                return {"status": "success", "message": "No target stocks"}
            
            # 过滤已计算的股票 (避免重复计算)
            if not force:
                async with self.db_manager.get_session() as session:
                    existing_stmt = select(StockScoreResult.code).where(StockScoreResult.trade_date == target_date)
                    existing_res = await session.execute(existing_stmt)
                    existing_codes = set(existing_res.scalars().all())
                
                original_count = len(target_codes)
                target_codes = [c for c in target_codes if c not in existing_codes]
                skipped_count = original_count - len(target_codes)
                
                if skipped_count > 0:
                    logger.info(f"跳过 {skipped_count} 只已计算评分的股票 (目标日期: {target_date})")
            
            if not target_codes:
                logger.info(f"所有目标股票在 {target_date} 的评分均已存在，无需计算")
                return {"status": "success", "message": "All stocks already scored", "count": 0}

            # 获取股票池映射
            pool_map = await self.repository.get_stock_pool_map()
            
            # --- 1.5 执行异动分析 (生成标签) ---
            # 用户要求: 定时任务执行评分时，需要先执行异动分析生成标签
            logger.info(f"开始执行异动分析(生成标签) - 目标日期: {target_date}, 股票数量: {len(target_codes)}")
            
            async def process_tag_generation(code):
                retries = 3
                for attempt in range(retries):
                    try:
                        async with self.db_manager.get_session() as session:
                            await VolumeAnalysisService.generate_daily_tags(code, target_date, session)
                            await session.commit()
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if ("Deadlock" in error_msg or "deadlock" in error_msg) and attempt < retries - 1:
                            # logger.warning(f"Deadlock processing {code}, retrying {attempt+1}/{retries}")
                            await asyncio.sleep(0.5 + attempt * 0.5) # Backoff
                            continue
                        logger.error(f"Generate tags failed for {code}: {e}")
                        break

            # 分批执行以控制并发 (降低并发数以减少死锁)
            analysis_batch_size = 10  
            for i in range(0, len(target_codes), analysis_batch_size):
                batch = target_codes[i:i+analysis_batch_size]
                tasks = [process_tag_generation(code) for code in batch]
                await asyncio.gather(*tasks)
                if (i + analysis_batch_size) % 100 == 0:
                    logger.info(f"已完成 {i + analysis_batch_size}/{len(target_codes)} 只股票的异动分析")
            
            logger.info("异动分析(标签生成) 完成，开始计算评分...")

            # 获取股票标签映射 (批量获取)
            # 考虑到codes可能很多，这里应该分批获取或者全部获取
            # 如果codes数量很大(>1000)，in_ clause可能会报错
            # 这里简单处理：如果超过1000个，分批查询
            tag_map = {}
            batch_size = 1000
            for i in range(0, len(target_codes), batch_size):
                batch = target_codes[i:i+batch_size]
                batch_tags = await self._get_stock_tags(batch)
                tag_map.update(batch_tags)
            
            # 记录任务开始
            await self.repository.save_task_log({
                "task_name": f"calculate_scores_{target_date}",
                "status": "running",
                "message": f"Start calculating for {len(target_codes)} stocks"
            })
            
            success_count = 0
            results = []
            
            # 3. 遍历计算
            # 预取数据优化：
            # 需要过去21天的数据(计算20天地量 + 倍量需要昨日数据)
            # 为了简单，还是逐个或分批获取
            
            for i, code in enumerate(target_codes):
                # 获取过去25天的数据(留余量)
                history = await self.repository.get_daily_data(
                    code, 
                    target_date - timedelta(days=40), 
                    target_date
                )
                
                if not history:
                    continue
                    
                # 确保最后一条是target_date
                if history[-1].trade_date != target_date:
                    # 如果当天没有数据，可能是停牌或数据未同步
                    continue
                
                # 开始计算规则
                # current_data = history[-1] # Not used if we rely on tags
                scores = {}
                total_score = Decimal(0)
                
                # --- 规则计算 ---
                # 仅基于标签计算 (Volume analysis tags are pre-calculated and stored in stock_tag_relations)
                # 用户要求: 成交量异动分析表是根据标签表的来计算的，不用旧的评分公式
                
                # Tag Scores
                stock_tags = tag_map.get(code, [])
                for tag_info in stock_tags:
                    tag_name = tag_info["name"]
                    tag_score = Decimal(str(tag_info["score"]))
                    
                    if tag_score > 0:
                        score_key = f"tag_{tag_name}"
                        if score_key not in scores:
                            scores[score_key] = float(tag_score)
                            total_score += tag_score
                
                # 保存结果
                results.append({
                    "code": code,
                    "trade_date": target_date,
                    "rule_scores": scores,
                    "total_score": total_score,
                    "ranking": 0, # 暂时不排，后续更新
                    "pool_type": pool_map.get(code, "unknown")
                })
                success_count += 1
                
            if results:
                # 排序并计算排名
                results.sort(key=lambda x: x["total_score"], reverse=True)
                for rank, res in enumerate(results, 1):
                    res["ranking"] = rank
                    
                # 批量保存
                await self.repository.save_stock_scores(results)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录任务完成
            await self.repository.save_task_log({
                "task_name": f"calculate_scores_{target_date}",
                "status": "success",
                "message": f"Calculated scores for {success_count} stocks. Saved {len(results)} results.",
                "duration": int(duration)
            })
            
            logger.info(f"评分计算完成: 成功 {success_count} 条, 耗时 {duration:.2f} 秒")
            
            return {
                "status": "success",
                "count": success_count,
                "duration": duration
            }
            
        except Exception as e:
            logger.error(f"评分计算失败: {e}")
            await self.repository.save_task_log({
                "task_name": f"calculate_scores_{target_date}",
                "status": "failed",
                "message": str(e)
            })
            return {"status": "failed", "error": str(e)}
