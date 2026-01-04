#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫数据仓库
提供爬虫目标和结果的数据访问方法
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .base import BaseRepository
from ..models.crawler import CrawlerTarget, CrawlerResult


class CrawlerTargetRepository(BaseRepository[CrawlerTarget]):
    """爬虫目标仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CrawlerTarget, session)
    
    async def find_by_platform(self, platform: str) -> List[CrawlerTarget]:
        """根据平台查找目标"""
        return await self.find_all_by_field("platform", platform)
    
    async def find_by_filters(self, platform: Optional[str] = None, name: Optional[str] = None, url: Optional[str] = None) -> List[CrawlerTarget]:
        """根据条件筛选目标"""
        try:
            query = select(CrawlerTarget)
            
            if platform:
                query = query.where(CrawlerTarget.platform == platform)
            if name:
                query = query.where(CrawlerTarget.name.ilike(f"%{name}%"))
            if url:
                query = query.where(CrawlerTarget.url.ilike(f"%{url}%"))
                
            query = query.order_by(desc(CrawlerTarget.created_at))
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"筛选目标失败: {e}")
            raise

    async def find_active_targets(self, platform: Optional[str] = None) -> List[CrawlerTarget]:
        """查找活跃目标"""
        try:
            query = select(CrawlerTarget).where(CrawlerTarget.is_active == True)
            
            if platform:
                query = query.where(CrawlerTarget.platform == platform)
                
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"查找活跃目标失败: {e}")
            raise


class CrawlerResultRepository(BaseRepository[CrawlerResult]):
    """爬虫结果仓库"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CrawlerResult, session)
        
    async def find_by_platform(self, platform: str, limit: int = 100) -> List[CrawlerResult]:
        """根据平台查找结果"""
        try:
            query = select(CrawlerResult)\
                .where(CrawlerResult.platform == platform)\
                .order_by(desc(CrawlerResult.crawled_at))\
                .limit(limit)
                
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据平台查找结果失败: {e}")
            raise

    async def find_by_target_id(self, target_id: int, limit: int = 100) -> List[CrawlerResult]:
        """根据目标ID查找结果"""
        try:
            query = select(CrawlerResult)\
                .where(CrawlerResult.target_id == target_id)\
                .order_by(desc(CrawlerResult.crawled_at))\
                .limit(limit)
                
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"根据目标ID查找结果失败: {e}")
            raise
