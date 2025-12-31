#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票池服务
负责基于问财数据自动维护监控股票池
"""

import logging
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.monitor_repository import MonitorRepository
from ..services.wencai_service import WencaiService
from ..services.tonghuashun_mcp_client import TongHuaShunMCPClient
from ..services.monitor_service import MonitorService
from ..database import db_manager
from app.config.logging import get_logger

# 配置日志
logger = get_logger(__name__)

class StockPoolService:
    """股票池服务"""
    
    def __init__(self):
        self.mcp_client = TongHuaShunMCPClient()
        
    async def refresh_pool_by_wencai(self, query: str, priority: int = 5, clear_existing: bool = False) -> Dict[str, Any]:
        """
        使用问财查询结果刷新监控池
        
        Args:
            query: 问财查询语句 (e.g. "量比大于3, 涨幅大于3%")
            priority: 入池股票的优先级
            clear_existing: 是否清空现有低优先级的监控
            
        Returns:
            Dict: 执行结果统计
        """
        logger.info(f"开始执行问财选股刷新: {query}")
        
        try:
            # 1. 构建问财URL
            encoded_query = urllib.parse.quote(query)
            url = f"http://www.iwencai.com/stockpick/search?typed=1&preParams=&ts=1&f=1&qs=result_original&selfsectsn=&querytype=stock&searchfilter=&tid=stockpick&w={encoded_query}"
            
            # 2. 获取页面内容
            result = await self.mcp_client.chrome_get_web_content(
                url=url,
                wait_time=8000, # 问财加载较慢
                timeout=60000
            )
            
            if not result.get('content'):
                raise Exception(f"获取问财页面失败: {result.get('error')}")
                
            html_content = result['content']
            
            async with db_manager.get_session() as session:
                wencai_service = WencaiService(session)
                monitor_service = MonitorService(session)
                
                # 3. 解析数据
                stocks = wencai_service.parse_html_table(html_content)
                if not stocks:
                    logger.warning("未解析到任何股票数据")
                    return {'status': 'empty', 'count': 0}
                
                logger.info(f"解析到 {len(stocks)} 只股票")
                
                # 4. 更新监控池
                added_count = 0
                updated_count = 0
                errors = []
                
                for stock in stocks:
                    code = stock.get('stock_code')
                    if not code: continue
                    
                    try:
                        # 尝试添加监控
                        # 如果已存在，update_monitor_priority 会更新优先级
                        # 这里我们直接调用 add_monitor，它内部有检查逻辑
                        # 但为了更精细控制，我们先检查是否存在
                        
                        # 既然 MonitorService 封装较好，直接利用其 batch_add 也可以，
                        # 但为了处理 "clear_existing" 逻辑，我们需要手动控制
                        
                        await monitor_service.add_monitor(
                            stock_code=code,
                            priority=priority,
                            auto_create_stock=True
                        )
                        added_count += 1
                        
                    except Exception as e:
                        errors.append(f"{code}: {e}")
                
                # 5. (可选) 清理逻辑
                # 例如：将不在本次结果中，但之前由该策略添加的股票移除
                # 这需要我们在 monitor_list 表中记录 source 或 tag，目前暂不支持
                
                await session.commit()
                
                return {
                    'status': 'success',
                    'total_parsed': len(stocks),
                    'added_updated': added_count,
                    'errors': errors
                }
                
        except Exception as e:
            logger.error(f"问财选股刷新失败: {e}")
            return {'status': 'error', 'message': str(e)}

# 单例
stock_pool_service = StockPoolService()
