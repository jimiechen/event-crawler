#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图分析服务
支持三龙聚首指标、K/D信号、主力控盘识别
"""

import base64
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from loguru import logger

from ..models.screenshot_analysis import ScreenshotAnalysis
from ..models.stock import StockData
from ..ai.prompts import get_prompt
from ..ai.trae_client import trae_client


class ScreenshotAnalysisService:
    """截图分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_analysis_task(
        self, 
        request_data: Dict[str, Any]
    ) -> ScreenshotAnalysis:
        """创建分析任务"""
        # 计算图片大小
        image_data = request_data.get("image_base64", "")
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        try:
            image_bytes = base64.b64decode(image_data)
            image_size = len(image_bytes)
        except Exception:
            image_size = 0
        
        # 创建记录
        analysis = ScreenshotAnalysis(
            task_id=request_data.get("task_id"),
            batch_id=request_data.get("batch_id"),
            stock_code=request_data.get("stock_code"),
            stock_name=request_data.get("stock_name"),
            screenshot_type=request_data.get("screenshot_type", "tlby"),
            image_data=request_data.get("image_base64"),
            image_format=request_data.get("image_format", "png"),
            image_size=image_size,
            source_ip=request_data.get("source_ip"),
            agent_id=request_data.get("agent_id"),
            status="pending"
        )
        
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        
        logger.info(f"截图分析任务已创建: id={analysis.id}, task_id={analysis.task_id}")
        return analysis
    
    async def analyze_screenshot(self, analysis_id: int) -> ScreenshotAnalysis:
        """执行截图分析"""
        analysis = await self.db.get(ScreenshotAnalysis, analysis_id)
        if not analysis:
            raise ValueError(f"分析记录不存在: {analysis_id}")
        
        analysis.status = "analyzing"
        await self.db.commit()
        
        try:
            # 1. 调用AI识别（通过Trae CLI或其他方式）
            ai_result = await self._call_ai_analysis(analysis)
            
            # 2. 解析AI结果
            self._parse_and_save_ai_result(analysis, ai_result)
            
            # 3. 数据比对
            verification = await self._verify_with_db_data(analysis)
            analysis.verification_result = verification
            analysis.is_data_match = verification.get("is_match")
            analysis.match_confidence = Decimal(str(verification.get("confidence", 0)))
            
            # 4. 更新状态
            analysis.status = "completed"
            analysis.analyzed_at = datetime.now(timezone.utc)
            
            logger.info(f"截图分析完成: id={analysis_id}, pattern={analysis.detected_pattern}")
            
        except Exception as e:
            analysis.status = "failed"
            analysis.error_message = str(e)
            logger.error(f"截图分析失败: {e}")
        
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis
    
    async def _call_ai_analysis(
        self, 
        analysis: ScreenshotAnalysis
    ) -> Dict[str, Any]:
        """调用AI分析截图"""
        # 获取提示词
        prompt = get_prompt(analysis.screenshot_type)
        
        logger.info(f"调用AI分析: task_id={analysis.task_id}, type={analysis.screenshot_type}")
        
        try:
            # 调用 Trae CLI 进行AI分析
            result = await trae_client.analyze_image(
                image_base64=analysis.image_data,
                prompt=prompt,
                model="kimi-k2.5"
            )
            
            # 如果解析失败，返回默认结果
            if result.get("parse_error"):
                logger.warning(f"AI结果解析失败，使用默认结果: {result.get('raw_output', '')[:200]}")
                return self._get_default_result(analysis)
            
            return result
            
        except Exception as e:
            logger.error(f"AI分析调用失败: {e}")
            return self._get_default_result(analysis)
    
    def _get_default_result(self, analysis: ScreenshotAnalysis) -> Dict[str, Any]:
        """获取默认结果"""
        return {
            "stock_code": analysis.stock_code,
            "stock_name": analysis.stock_name or "未知",
            "price": 0,
            "change_percent": 0,
            "volume": 0,
            "sanlong": {
                "trend_alert": 0,
                "volume_alert": 0,
                "mid_alert": 0,
                "short_alert": 0,
                "alert_count": 0,
                "all_red": False
            },
            "kd_signals": {
                "has_k_signal_today": False,
                "has_d_signal_today": False,
                "k_signal_count": 0,
                "d_signal_count": 0
            },
            "pattern": "unknown",
            "pattern_confidence": 0,
            "analysis_text": "AI分析失败，返回默认结果"
        }
    
    def _parse_and_save_ai_result(
        self, 
        analysis: ScreenshotAnalysis, 
        ai_result: Dict[str, Any]
    ):
        """解析并保存AI结果"""
        # 基础数据
        analysis.ai_price = Decimal(str(ai_result.get("price", 0)))
        analysis.ai_change_percent = Decimal(str(ai_result.get("change_percent", 0)))
        analysis.ai_volume = ai_result.get("volume")
        
        # 三龙聚首
        sanlong = ai_result.get("sanlong", {})
        analysis.sanlong_trend_alert = sanlong.get("trend_alert")
        analysis.sanlong_volume_alert = sanlong.get("volume_alert")
        analysis.sanlong_mid_alert = sanlong.get("mid_alert")
        analysis.sanlong_short_alert = sanlong.get("short_alert")
        analysis.sanlong_alert_count = sanlong.get("alert_count")
        analysis.sanlong_all_red = sanlong.get("all_red")
        
        # K/D信号
        kd = ai_result.get("kd_signals", {})
        analysis.has_k_signal_today = kd.get("has_k_signal_today")
        analysis.has_d_signal_today = kd.get("has_d_signal_today")
        analysis.k_signal_count = kd.get("k_signal_count")
        analysis.d_signal_count = kd.get("d_signal_count")
        
        # 主力控盘
        main_force = ai_result.get("main_force", {})
        analysis.main_force_buy_ratio = Decimal(str(main_force.get("main_force_buy_ratio", 0)))
        analysis.main_force_sell_ratio = Decimal(str(main_force.get("main_force_sell_ratio", 0)))
        analysis.retail_buy_ratio = Decimal(str(main_force.get("retail_buy_ratio", 0)))
        analysis.retail_sell_ratio = Decimal(str(main_force.get("retail_sell_ratio", 0)))
        
        # 形态
        analysis.detected_pattern = ai_result.get("pattern")
        analysis.pattern_confidence = Decimal(str(ai_result.get("pattern_confidence", 0)))
        analysis.ai_analysis_text = ai_result.get("analysis_text")
        
        # 完整结果
        analysis.ai_result = ai_result
        analysis.ai_model = "kimi-k2.5"
    
    async def _verify_with_db_data(
        self, 
        analysis: ScreenshotAnalysis
    ) -> Dict[str, Any]:
        """验证AI识别结果与数据库数据是否匹配"""
        differences = []
        
        # 查询数据库最新数据
        stmt = select(StockData).where(
            StockData.code == analysis.stock_code
        ).order_by(desc(StockData.timestamp)).limit(1)
        
        result = await self.db.execute(stmt)
        db_data = result.scalar_one_or_none()
        
        if not db_data:
            return {
                "is_match": None,
                "confidence": 0,
                "differences": [],
                "message": "数据库中无该股票数据"
            }
        
        # 价格比对 (允许1%误差)
        if analysis.ai_price and db_data.price:
            ai_price = float(analysis.ai_price)
            db_price = float(db_data.price)
            if db_price > 0 and abs(ai_price - db_price) / db_price > 0.01:
                differences.append({
                    "field": "price",
                    "ai_value": ai_price,
                    "db_value": db_price,
                    "diff_percent": round(abs(ai_price - db_price) / db_price * 100, 2)
                })
        
        # 涨跌幅比对 (允许0.5%误差)
        if analysis.ai_change_percent and db_data.change_percent:
            ai_change = float(analysis.ai_change_percent)
            db_change = float(db_data.change_percent)
            if abs(ai_change - db_change) > 0.5:
                differences.append({
                    "field": "change_percent",
                    "ai_value": ai_change,
                    "db_value": db_change,
                    "diff": round(abs(ai_change - db_change), 2)
                })
        
        # 计算置信度
        confidence = 1.0 if not differences else max(0, 1 - len(differences) * 0.2)
        
        return {
            "is_match": len(differences) == 0,
            "confidence": round(confidence, 2),
            "differences": differences,
            "db_data": {
                "price": float(db_data.price) if db_data.price else None,
                "change_percent": float(db_data.change_percent) if db_data.change_percent else None,
                "volume": db_data.volume
            }
        }
