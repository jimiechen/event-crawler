#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略服务
负责执行量化策略，判断是否触发告警
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.config.logging import get_logger
from .notification_service import notification_service

# 配置日志
logger = get_logger(__name__)

class StrategyService:
    """策略服务"""
    
    def __init__(self):
        # 缓存已触发的告警，避免重复发送 (key: stock_code, value: timestamp)
        self.triggered_alerts = {}
        # 告警冷却时间 (秒)
        self.alert_cooldown = 300 
        
    def check_signal(self, current_data: Dict[str, Any], strategy_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        检查是否触发策略信号 (无副作用)
        
        Returns:
            dict: {
                "is_triggered": bool,
                "trigger_reason": list,
                "metrics": dict
            }
        """
        # 1. 提取数据
        try:
            price = Decimal(str(current_data.get('current_price', 0)))
            # change_percent might be missing or 0
            change_percent = float(current_data.get('change_percent', 0))
        except (ValueError, TypeError):
            return {"is_triggered": False, "trigger_reason": [], "error": "Invalid data format"}

        # 2. 获取策略参数 (默认值)
        vol_ratio_threshold = 3.0
        price_change_threshold = 3.0 # 3%
        
        if strategy_config:
            vol_ratio_threshold = strategy_config.get('vol_ratio_threshold', vol_ratio_threshold)
            price_change_threshold = strategy_config.get('price_change_threshold', price_change_threshold)
        
        # 3. 计算/获取指标
        current_vol_ratio = 0.0
        if 'volume_ratio' in current_data:
             try:
                current_vol_ratio = float(current_data['volume_ratio'])
             except (ValueError, TypeError):
                pass
        
        # 4. 判定逻辑
        is_triggered = False
        trigger_reason = []
        
        # 逻辑 A: 量比突破
        if current_vol_ratio > vol_ratio_threshold:
            is_triggered = True
            trigger_reason.append(f"量比({current_vol_ratio}) > {vol_ratio_threshold}")
        
        # 逻辑 B: 价格突破 (结合量)
        if is_triggered and change_percent > price_change_threshold:
            trigger_reason.append(f"涨幅({change_percent}%) > {price_change_threshold}%")
        else:
            # If volume trigger but price not, reset trigger unless we have volume-only alerts
            # But the original logic was: if is_triggered (volume) AND price_change, then ALERT.
            # So if volume triggered but price didn't, it's NOT an alert.
            is_triggered = False
            trigger_reason = [] 

        return {
            "is_triggered": is_triggered,
            "trigger_reason": trigger_reason,
            "metrics": {
                "price": float(price),
                "change_percent": change_percent,
                "volume_ratio": current_vol_ratio
            }
        }

    async def analyze_tick(self, stock_code: str, current_data: Dict[str, Any], strategy_config: Optional[Dict] = None):
        """
        分析实时Tick数据
        """
        try:
            # 1. 检查信号
            result = self.check_signal(current_data, strategy_config)
            
            if result.get("error"):
                return

            is_triggered = result["is_triggered"]
            trigger_reason = result["trigger_reason"]
            
            if is_triggered:
                # 提取基础数据用于发送
                price = Decimal(str(current_data.get('current_price', 0)))
                volume = int(current_data.get('volume', 0))
                
                # 发送告警
                await self._trigger_alert(stock_code, price, volume, ", ".join(trigger_reason))
                
        except Exception as e:
            logger.error(f"策略分析失败 ({stock_code}): {e}")

    async def _trigger_alert(self, stock_code: str, price: Decimal, volume: int, reason: str):
        """触发告警"""
        now = datetime.now()
        last_alert_time = self.triggered_alerts.get(stock_code)
        
        # 检查冷却时间
        if last_alert_time and (now - last_alert_time).total_seconds() < self.alert_cooldown:
            return
            
        # 更新时间
        self.triggered_alerts[stock_code] = now
        
        # 构建消息
        title = f"🚀 股价异动提醒: {stock_code}"
        message = f"当前价格: {price}\n成交量: {volume}\n触发原因: {reason}"
        
        # 发送通知
        await notification_service.send_alert(
            title=title,
            message=message,
            level='warning',
            data={'stock_code': stock_code, 'price': str(price), 'volume': volume, 'reason': reason}
        )

# 单例
strategy_service = StrategyService()
