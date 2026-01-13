#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据一致性检查服务
用于验证全流程数据的一致性
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..models.stock_daily import StockScoreResult, StockDaily
from ..models.stock import StockInfo
from ..models.volume_analysis import StockVolumeBaseline
from ..database import db_manager
from ..services.redis_cache_service import redis_cache_service


class DataConsistencyService:
    """数据一致性检查服务"""
    
    def __init__(self):
        self.consistency_results = []
    
    async def check_all_consistency(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查所有数据一致性
        
        Returns:
            一致性检查结果字典
        """
        logger.info("开始数据一致性检查...")
        
        results = {
            'check_time': datetime.now(),
            'redis_consistency': await self._check_redis_consistency(session),
            'database_consistency': await self._check_database_consistency(session),
            'vectorized_calculation_consistency': await self._check_vectorized_calculation_consistency(session),
            'data_integrity': await self._check_data_integrity(session)
        }
        
        logger.info(f"数据一致性检查完成: {self._format_summary(results)}")
        
        return results
    
    async def _check_redis_consistency(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查Redis缓存与数据库的一致性
        """
        logger.info("检查Redis缓存一致性...")
        
        result = {
            'total_checked': 0,
            'consistent': 0,
            'inconsistent': [],
            'errors': []
        }
        
        try:
            # 获取所有有baseline的股票
            stmt = select(StockVolumeBaseline.code)
            db_result = await session.execute(stmt)
            codes = db_result.scalars().all()
            
            result['total_checked'] = len(codes)
            
            for code in codes:
                try:
                    # 从Redis获取baseline
                    redis_baseline = redis_cache_service.get_baseline(code)
                    
                    # 从数据库获取baseline
                    stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
                    db_baseline = await session.execute(stmt)
                    db_baseline = db_baseline.scalar_one_or_none()
                    
                    if redis_baseline and db_baseline:
                        # 检查关键字段是否一致
                        is_consistent = True
                        inconsistencies = []
                        
                        # 检查3倍量
                        redis_3x = redis_baseline.get('last_3x_close', {}).get('value')
                        db_3x = db_baseline.last_3x_close
                        if redis_3x != db_3x:
                            is_consistent = False
                            inconsistencies.append(f"3倍量: Redis={redis_3x}, DB={db_3x}")
                        
                        # 检查60日地量
                        redis_60d = redis_baseline.get('last_60d_low_vol', {}).get('value')
                        db_60d = db_baseline.last_60d_low_vol
                        if redis_60d != db_60d:
                            is_consistent = False
                            inconsistencies.append(f"60日地量: Redis={redis_60d}, DB={db_60d}")
                        
                        if is_consistent:
                            result['consistent'] += 1
                        else:
                            result['inconsistent'].append({
                                'code': code,
                                'inconsistencies': inconsistencies
                            })
                
                except Exception as e:
                    result['errors'].append({
                        'code': code,
                        'error': str(e)
                    })
                    logger.error(f"检查 {code} Redis一致性失败: {e}")
            
            logger.info(f"Redis一致性检查完成: 总计={result['total_checked']}, 一致={result['consistent']}, 不一致={len(result['inconsistent'])}")
            
        except Exception as e:
            logger.error(f"Redis一致性检查失败: {e}")
            result['errors'].append({'error': str(e)})
        
        return result
    
    async def _check_database_consistency(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查数据库表之间的数据一致性
        """
        logger.info("检查数据库表一致性...")
        
        result = {
            'stock_info_vs_score_result': await self._check_stock_info_vs_score_result(session),
            'stock_daily_completeness': await self._check_stock_daily_completeness(session),
            'baseline_completeness': await self._check_baseline_completeness(session)
        }
        
        return result
    
    async def _check_stock_info_vs_score_result(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查stock_info.volume_anomaly_score与stock_score_result总分是否一致
        """
        result = {
            'total_checked': 0,
            'consistent': 0,
            'inconsistent': []
        }
        
        try:
            # 获取最新的stock_score_result记录
            latest_date = date.today()
            
            stmt = text(f"""
                SELECT 
                    s.code,
                    s.volume_anomaly_score as info_score,
                    r.total_score as result_score
                FROM stock_info s
                LEFT JOIN stock_score_result r ON s.code = r.code AND r.trade_date = '{latest_date}'
                WHERE s.volume_anomaly_score IS NOT NULL
            """)
            
            db_result = await session.execute(stmt)
            rows = db_result.fetchall()
            
            result['total_checked'] = len(rows)
            
            for row in rows:
                code, info_score, result_score = row
                
                if result_score is not None:
                    # 比较分数（允许小数点误差）
                    if abs(float(info_score) - float(result_score)) > 0.01:
                        result['inconsistent'].append({
                            'code': code,
                            'info_score': float(info_score),
                            'result_score': float(result_score),
                            'diff': abs(float(info_score) - float(result_score))
                        })
                    else:
                        result['consistent'] += 1
            
            logger.info(f"stock_info vs score_result检查完成: 总计={result['total_checked']}, 一致={result['consistent']}, 不一致={len(result['inconsistent'])}")
        
        except Exception as e:
            logger.error(f"stock_info vs score_result检查失败: {e}")
        
        return result
    
    async def _check_stock_daily_completeness(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查stock_daily数据完整性
        """
        result = {
            'total_stocks': 0,
            'stocks_with_data': 0,
            'stocks_without_data': []
        }
        
        try:
            # 获取所有活跃股票
            stmt = select(StockInfo.code).where(StockInfo.is_active == True)
            db_result = await session.execute(stmt)
            codes = db_result.scalars().all()
            
            result['total_stocks'] = len(codes)
            
            for code in codes:
                # 检查是否有最近的数据
                stmt = select(func.count(StockDaily.id)).where(
                    StockDaily.code == code,
                    StockDaily.trade_date >= date.today() - timedelta(days=7)
                )
                db_result = await session.execute(stmt)
                count = db_result.scalar()
                
                if count > 0:
                    result['stocks_with_data'] += 1
                else:
                    result['stocks_without_data'].append(code)
            
            logger.info(f"stock_daily完整性检查完成: 总计={result['total_stocks']}, 有数据={result['stocks_with_data']}, 无数据={len(result['stocks_without_data'])}")
        
        except Exception as e:
            logger.error(f"stock_daily完整性检查失败: {e}")
        
        return result
    
    async def _check_baseline_completeness(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查baseline数据完整性
        """
        result = {
            'total_stocks': 0,
            'stocks_with_baseline': 0,
            'stocks_without_baseline': []
        }
        
        try:
            # 获取所有活跃股票
            stmt = select(StockInfo.code).where(StockInfo.is_active == True)
            db_result = await session.execute(stmt)
            codes = db_result.scalars().all()
            
            result['total_stocks'] = len(codes)
            
            for code in codes:
                # 检查是否有baseline
                stmt = select(StockVolumeBaseline).where(StockVolumeBaseline.code == code)
                db_result = await session.execute(stmt)
                baseline = db_result.scalar_one_or_none()
                
                if baseline:
                    result['stocks_with_baseline'] += 1
                else:
                    result['stocks_without_baseline'].append(code)
            
            logger.info(f"baseline完整性检查完成: 总计={result['total_stocks']}, 有baseline={result['stocks_with_baseline']}, 无baseline={len(result['stocks_without_baseline'])}")
        
        except Exception as e:
            logger.error(f"baseline完整性检查失败: {e}")
        
        return result
    
    async def _check_vectorized_calculation_consistency(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查向量化计算结果的一致性
        """
        logger.info("检查向量化计算一致性...")
        
        result = {
            'total_checked': 0,
            'consistent': 0,
            'inconsistent': [],
            'errors': []
        }
        
        try:
            # 随机抽取10只股票进行验证
            stmt = select(StockInfo.code).where(StockInfo.is_active == True).limit(10)
            db_result = await session.execute(stmt)
            codes = db_result.scalars().all()
            
            result['total_checked'] = len(codes)
            
            from ..services.volume_analysis_service import VolumeAnalysisService
            
            for code in codes:
                try:
                    # 重新计算向量化结果
                    analysis_result = await VolumeAnalysisService.analyze_stock(code, session=session)
                    
                    if analysis_result:
                        # 获取数据库中的结果
                        stmt = select(StockScoreResult).where(
                            StockScoreResult.code == code,
                            StockScoreResult.trade_date == date.today()
                        )
                        db_result = await session.execute(stmt)
                        db_score = db_result.scalar_one_or_none()
                        
                        if db_score:
                            # 比较总分
                            calc_score = analysis_result.get('total_score', 0)
                            db_score_value = float(db_score.total_score)
                            
                            if abs(calc_score - db_score_value) > 0.01:
                                result['inconsistent'].append({
                                    'code': code,
                                    'calculated_score': calc_score,
                                    'db_score': db_score_value,
                                    'diff': abs(calc_score - db_score_value)
                                })
                            else:
                                result['consistent'] += 1
                
                except Exception as e:
                    result['errors'].append({
                        'code': code,
                        'error': str(e)
                    })
                    logger.error(f"检查 {code} 向量化计算一致性失败: {e}")
            
            logger.info(f"向量化计算一致性检查完成: 总计={result['total_checked']}, 一致={result['consistent']}, 不一致={len(result['inconsistent'])}")
        
        except Exception as e:
            logger.error(f"向量化计算一致性检查失败: {e}")
            result['errors'].append({'error': str(e)})
        
        return result
    
    async def _check_data_integrity(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查数据完整性
        """
        logger.info("检查数据完整性...")
        
        result = {
            'duplicate_records': await self._check_duplicate_records(session),
            'null_values': await self._check_null_values(session),
            'date_range': await self._check_date_range(session)
        }
        
        return result
    
    async def _check_duplicate_records(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查重复记录
        """
        result = {
            'stock_daily_duplicates': 0,
            'score_result_duplicates': 0
        }
        
        try:
            # 检查stock_daily重复记录
            stmt = text("""
                SELECT COUNT(*) - COUNT(DISTINCT CONCAT(code, trade_date)) as duplicates
                FROM stock_daily
            """)
            db_result = await session.execute(stmt)
            result['stock_daily_duplicates'] = db_result.scalar()
            
            # 检查stock_score_result重复记录
            stmt = text("""
                SELECT COUNT(*) - COUNT(DISTINCT CONCAT(code, trade_date)) as duplicates
                FROM stock_score_result
            """)
            db_result = await session.execute(stmt)
            result['score_result_duplicates'] = db_result.scalar()
            
            logger.info(f"重复记录检查完成: stock_daily={result['stock_daily_duplicates']}, score_result={result['score_result_duplicates']}")
        
        except Exception as e:
            logger.error(f"重复记录检查失败: {e}")
        
        return result
    
    async def _check_null_values(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查空值
        """
        result = {
            'stock_daily_nulls': {},
            'score_result_nulls': {}
        }
        
        try:
            # 检查stock_daily空值
            for column in ['open', 'close', 'high', 'low', 'vol']:
                stmt = text(f"SELECT COUNT(*) FROM stock_daily WHERE {column} IS NULL")
                db_result = await session.execute(stmt)
                count = db_result.scalar()
                if count > 0:
                    result['stock_daily_nulls'][column] = count
            
            # 检查stock_score_result空值
            for column in ['total_score']:
                stmt = text(f"SELECT COUNT(*) FROM stock_score_result WHERE {column} IS NULL")
                db_result = await session.execute(stmt)
                count = db_result.scalar()
                if count > 0:
                    result['score_result_nulls'][column] = count
            
            logger.info(f"空值检查完成: stock_daily={result['stock_daily_nulls']}, score_result={result['score_result_nulls']}")
        
        except Exception as e:
            logger.error(f"空值检查失败: {e}")
        
        return result
    
    async def _check_date_range(self, session: AsyncSession) -> Dict[str, Any]:
        """
        检查日期范围
        """
        result = {
            'stock_daily_min_date': None,
            'stock_daily_max_date': None,
            'score_result_min_date': None,
            'score_result_max_date': None
        }
        
        try:
            # 检查stock_daily日期范围
            stmt = text("SELECT MIN(trade_date), MAX(trade_date) FROM stock_daily")
            db_result = await session.execute(stmt)
            row = db_result.fetchone()
            if row:
                result['stock_daily_min_date'] = row[0]
                result['stock_daily_max_date'] = row[1]
            
            # 检查stock_score_result日期范围
            stmt = text("SELECT MIN(trade_date), MAX(trade_date) FROM stock_score_result")
            db_result = await session.execute(stmt)
            row = db_result.fetchone()
            if row:
                result['score_result_min_date'] = row[0]
                result['score_result_max_date'] = row[1]
            
            logger.info(f"日期范围检查完成: stock_daily=[{result['stock_daily_min_date']}, {result['stock_daily_max_date']}], score_result=[{result['score_result_min_date']}, {result['score_result_max_date']}]")
        
        except Exception as e:
            logger.error(f"日期范围检查失败: {e}")
        
        return result
    
    def _format_summary(self, results: Dict[str, Any]) -> str:
        """
        格式化一致性检查摘要
        """
        summary = []
        
        # Redis一致性
        redis = results.get('redis_consistency', {})
        summary.append(f"Redis: {redis.get('consistent', 0)}/{redis.get('total_checked', 0)} 一致")
        
        # 数据库一致性
        db_cons = results.get('database_consistency', {})
        info_vs_score = db_cons.get('stock_info_vs_score_result', {})
        summary.append(f"stock_info vs score_result: {info_vs_score.get('consistent', 0)}/{info_vs_score.get('total_checked', 0)} 一致")
        
        # 向量化计算一致性
        vec_cons = results.get('vectorized_calculation_consistency', {})
        summary.append(f"向量化计算: {vec_cons.get('consistent', 0)}/{vec_cons.get('total_checked', 0)} 一致")
        
        # 数据完整性
        integrity = results.get('data_integrity', {})
        dup = integrity.get('duplicate_records', {})
        summary.append(f"重复记录: stock_daily={dup.get('stock_daily_duplicates', 0)}, score_result={dup.get('score_result_duplicates', 0)}")
        
        return ', '.join(summary)


# 全局单例
data_consistency_service = DataConsistencyService()
