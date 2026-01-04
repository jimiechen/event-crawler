#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie服务
处理Cookie的存储和检索
"""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cookie import ChromeCookie

logger = logging.getLogger(__name__)

class CookieService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_cookies(self, domain: str, cookies: List[Dict[str, Any]]) -> bool:
        """
        同步Cookie到数据库
        如果存在则更新，不存在则插入
        """
        try:
            cookies_json = json.dumps(cookies)
            
            # 使用upsert逻辑
            stmt = insert(ChromeCookie).values(
                domain=domain,
                cookies_json=cookies_json
            ).on_duplicate_key_update(
                cookies_json=cookies_json
            )
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            logger.info(f"Successfully synced cookies for domain: {domain}")
            return True
        except Exception as e:
            logger.error(f"Failed to sync cookies for {domain}: {e}")
            await self.db.rollback()
            raise e

    async def get_cookies(self, domain: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取指定域名的Cookie
        """
        try:
            # 尝试精确匹配
            stmt = select(ChromeCookie).where(ChromeCookie.domain == domain)
            result = await self.db.execute(stmt)
            cookie_record = result.scalar_one_or_none()
            
            if cookie_record:
                return json.loads(cookie_record.cookies_json)
            
            # 尝试模糊匹配 (比如传入 .baidu.com 匹配 baidu.com)
            # 或者传入 baidu.com 匹配 .baidu.com
            # 这里简单起见，先只做精确匹配。如果需要模糊匹配，可以后续添加。
            # 用户之前的Redis实现中有 scan 模糊匹配，这里可以用 LIKE
            
            stmt = select(ChromeCookie).where(ChromeCookie.domain.like(f"%{domain}%"))
            result = await self.db.execute(stmt)
            cookie_record = result.scalar_one_or_none()
            
            if cookie_record:
                return json.loads(cookie_record.cookies_json)
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cookies for {domain}: {e}")
            raise e
