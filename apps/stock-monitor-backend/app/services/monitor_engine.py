#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票监控引擎
核心调度模块，负责协调数据抓取、策略分析和数据存储
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from ..repositories.monitor_repository import MonitorRepository
from ..repositories.stock_repository import StockDataRepository
from ..services.tonghuashun_mcp_client import TongHuaShunMCPClient
from ..services.strategy_service import strategy_service
from ..database import db_manager

# 配置日志
logger = get_logger(__name__)

class StockMonitorEngine:
    """股票监控引擎"""
    
    def __init__(self, mcp_client: Optional[TongHuaShunMCPClient] = None):
        self.mcp_client = mcp_client or TongHuaShunMCPClient()
        self.is_running = False
        self.monitor_interval = 5  # 默认5秒
        
    async def start(self):
        """启动监控引擎"""
        if self.is_running:
            logger.warning("监控引擎已经在运行中")
            return
            
        self.is_running = True
        logger.info("启动股票监控引擎...")
        
        while self.is_running:
            try:
                async with db_manager.get_session() as session:
                    await self._process_cycle(session)
            except Exception as e:
                logger.error(f"监控循环发生错误: {e}")
                # 发生错误时等待较长时间，避免死循环轰炸
                await asyncio.sleep(10)
                
            # 等待下一次循环
            if self.is_running:
                await asyncio.sleep(self.monitor_interval)
                
        logger.info("股票监控引擎已停止")

    async def stop(self):
        """停止监控引擎"""
        self.is_running = False
        logger.info("正在停止监控引擎...")

    async def _process_cycle(self, session: AsyncSession):
        """执行一次监控循环"""
        monitor_repo = MonitorRepository(session)
        stock_data_repo = StockDataRepository(session)
        
        # 1. 获取活跃监控列表
        active_monitors = await monitor_repo.find_active_monitors()
        if not active_monitors:
            logger.debug("当前没有活跃的监控股票")
            return
            
        stock_codes = [m.code for m in active_monitors]
        
        # 2. 获取实时行情
        # 注意：同花顺接口可能限制单次查询数量，如果数量过多需要分批
        # 这里假设暂时不超过限制 (如50个)
        batch_size = 20
        for i in range(0, len(stock_codes), batch_size):
            batch_codes = stock_codes[i:i + batch_size]
            await self._process_batch(session, batch_codes, stock_data_repo)

    async def _process_batch(self, session: AsyncSession, codes: List[str], repo: StockDataRepository):
        """处理一批股票"""
        try:
            result = await self.mcp_client.get_stock_realtime_data(codes)
            
            if not result.get('success'):
                logger.warning(f"获取实时行情失败: {result.get('error')}")
                return
                
            stock_data_list = result.get('stock_data', [])
            
            for data in stock_data_list:
                # 3. 策略分析
                # 注意：这里不需要等待策略分析完成，可以使用 asyncio.create_task 异步执行
                # 但为了简单起见，且策略计算量小，暂时同步调用
                await strategy_service.analyze_tick(data['code'], data)
                
                # 4. 数据入库 (可选，如果需要保存Tick级别数据)
                # 考虑到数据量，可能只保存分钟级或重要变动
                # 这里暂时实现为保存所有抓取到的数据
                await self._save_stock_data(repo, data)
                
            # 提交事务
            await session.commit()
            
        except Exception as e:
            logger.error(f"批次处理失败 {codes}: {e}")
            await session.rollback()

    async def _save_stock_data(self, repo: StockDataRepository, data: Dict[str, Any]):
        """保存股票数据"""
        try:
            # 构造模型数据
            # 注意：StockData 模型字段需要匹配
            stock_data = {
                'code': data['code'],
                'price': data['current_price'],
                'change_percent': data['change_percent'],
                'volume': data['volume'],
                'turnover': data['turnover'],
                'timestamp': datetime.now().date(), # 简化处理，实际应使用行情时间
                'request_timestamp': str(int(datetime.now().timestamp()))
            }
            
            # 某些字段可能在实时接口中不存在，需要处理默认值
            if 'open' in data: stock_data['open_price'] = data['open']
            if 'high' in data: stock_data['high'] = data['high']
            if 'low' in data: stock_data['low'] = data['low']
            
            await repo.create(stock_data)
            
        except Exception as e:
            logger.error(f"数据保存失败 {data.get('code')}: {e}")
            # 不抛出异常，避免影响其他股票处理

# 单例
monitor_engine = StockMonitorEngine()
