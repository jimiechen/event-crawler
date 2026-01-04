#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie服务
处理Cookie的存储和检索
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
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

    async def get_all_cookies(self) -> List[Dict[str, Any]]:
        """获取所有Cookie记录"""
        try:
            stmt = select(ChromeCookie)
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "domain": r.domain,
                    "count": len(json.loads(r.cookies_json)) if r.cookies_json else 0,
                    "xpath_config": r.xpath_config,
                    "is_valid": r.is_valid,
                    "updated_at": r.updated_at,
                    "account_name": r.account_name,
                    "test_url": r.test_url,
                    "status": r.status,
                    "last_checked_at": r.last_checked_at
                } 
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to get all cookies: {e}")
            raise e

    async def update_cookie(self, id: int, data: Dict[str, Any]) -> bool:
        """更新Cookie记录"""
        try:
            stmt = select(ChromeCookie).where(ChromeCookie.id == id)
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if not record:
                return False
                
            if "xpath_config" in data:
                record.xpath_config = data["xpath_config"]
            if "is_valid" in data:
                record.is_valid = data["is_valid"]
            if "domain" in data:
                record.domain = data["domain"]
            if "cookies_json" in data:
                record.cookies_json = data["cookies_json"]
            if "account_name" in data:
                record.account_name = data["account_name"]
            if "test_url" in data:
                record.test_url = data["test_url"]
            if "status" in data:
                record.status = data["status"]
            if "last_checked_at" in data:
                record.last_checked_at = data["last_checked_at"]
                
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update cookie {id}: {e}")
            await self.db.rollback()
            raise e

    async def delete_cookie(self, id: int) -> bool:
        """删除Cookie记录"""
        try:
            stmt = select(ChromeCookie).where(ChromeCookie.id == id)
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if not record:
                return False
                
            await self.db.delete(record)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete cookie {id}: {e}")
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

    async def update_status_by_domain(self, domain: str, status: str, is_valid: bool = None) -> bool:
        """根据域名更新状态"""
        try:
            stmt = select(ChromeCookie).where(ChromeCookie.domain.like(f"%{domain}%"))
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if not record:
                return False
                
            record.status = status
            if is_valid is not None:
                record.is_valid = is_valid
            record.last_checked_at = datetime.now()
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update cookie status for {domain}: {e}")
            await self.db.rollback()
            return False
