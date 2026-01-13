#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话服务
处理平台会话的upsert、获取和验证
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import PlatformSession
from app.services.cookie_service import CookieService

logger = logging.getLogger(__name__)


class SessionService:
    """会话服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_session(
        self,
        platform_id: str,
        user_id: str,
        account_name: str,
        cookies: List[Dict[str, Any]],
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建或更新会话
        :param platform_id: 平台标识
        :param user_id: 用户ID/账号标识
        :param account_name: 账号名称/昵称
        :param cookies: Cookie列表
        :param user_agent: User-Agent
        :return: 会话信息
        """
        try:
            cookies_json = json.dumps(cookies)
            
            # 查找是否已存在该会话
            stmt = select(PlatformSession).where(
                PlatformSession.platform_id == platform_id,
                PlatformSession.user_id == user_id
            )
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                # 更新现有会话
                session.cookies_json = cookies_json
                session.account_name = account_name
                if user_agent:
                    session.user_agent = user_agent
                session.status = "active"
                session.health_score = 100
                session.last_verified_at = datetime.now()
                session.last_used_at = datetime.now()
                
                logger.info(f"更新会话成功: {platform_id}/{user_id}")
            else:
                # 创建新会话
                session = PlatformSession(
                    platform_id=platform_id,
                    user_id=user_id,
                    account_name=account_name,
                    cookies_json=cookies_json,
                    user_agent=user_agent,
                    status="active",
                    health_score=100,
                    last_verified_at=datetime.now(),
                    last_used_at=datetime.now()
                )
                self.db.add(session)
                logger.info(f"创建会话成功: {platform_id}/{user_id}")
            
            await self.db.flush()
            
            # 提前提取返回值，避免后续操作导致session过期或触发同步IO
            # 注意：commit()会默认expire所有对象，导致后续访问属性时触发IO
            # 在异步模式下，如果在commit后访问属性且未显式refresh，会导致greenlet错误
            # 因此我们在commit前提取所有需要的数据
            result_data = {
                "id": session.id,
                "platform_id": session.platform_id,
                "user_id": session.user_id,
                "account_name": session.account_name,
                "status": session.status,
                "health_score": session.health_score
            }
            
            await self.db.commit()

            
            # 同步更新到Cookie表，以便在Cookie管理界面显示
            try:
                cookie_service = CookieService(self.db)
                # 使用platform_id作为domain，或者如果需要真实域名，需要查询Platform表
                # 这里为了简化，直接使用platform_id作为标识
                await cookie_service.sync_cookies(platform_id, cookies)
                # 同时更新Cookie状态
                await cookie_service.update_status_by_domain(
                    platform_id, 
                    "active", 
                    is_valid=True
                )
            except Exception as e:
                logger.warning(f"同步Cookie失败 (不影响会话保存): {e}")

            return result_data
        except Exception as e:
            logger.error(f"upsert会话失败 {platform_id}/{user_id}: {e}")
            await self.db.rollback()
            raise e

    async def get_best_session(self, platform_id: str) -> Optional[Dict[str, Any]]:
        """
        获取最佳会话（健康度最高且状态为active）
        :param platform_id: 平台标识
        :return: 会话信息或None
        """
        try:
            stmt = (
                select(PlatformSession)
                .where(
                    PlatformSession.platform_id == platform_id,
                    PlatformSession.status == "active"
                )
                .order_by(PlatformSession.health_score.desc())
                .limit(1)
            )
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            return {
                "id": session.id,
                "platform_id": session.platform_id,
                "user_id": session.user_id,
                "account_name": session.account_name,
                "cookies_json": json.loads(session.cookies_json),
                "user_agent": session.user_agent,
                "health_score": session.health_score
            }
        except Exception as e:
            logger.error(f"获取最佳会话失败 {platform_id}: {e}")
            return None

    async def get_sessions_by_platform(self, platform_id: str) -> List[Dict[str, Any]]:
        """
        获取指定平台的所有会话
        :param platform_id: 平台标识
        :return: 会话列表
        """
        try:
            stmt = (
                select(PlatformSession)
                .where(PlatformSession.platform_id == platform_id)
                .order_by(PlatformSession.health_score.desc())
            )
            result = await self.db.execute(stmt)
            sessions = result.scalars().all()
            
            return [
                {
                    "id": s.id,
                    "platform_id": s.platform_id,
                    "user_id": s.user_id,
                    "account_name": s.account_name,
                    "status": s.status,
                    "health_score": s.health_score,
                    "last_verified_at": s.last_verified_at.isoformat() if s.last_verified_at else None,
                    "last_used_at": s.last_used_at.isoformat() if s.last_used_at else None
                }
                for s in sessions
            ]
        except Exception as e:
            logger.error(f"获取会话列表失败 {platform_id}: {e}")
            raise e

    async def verify_session(self, session_id: int, success: bool) -> bool:
        """
        验证会话并更新健康度
        :param session_id: 会话ID
        :param success: 是否验证成功
        :return: 是否更新成功
        """
        try:
            stmt = select(PlatformSession).where(PlatformSession.id == session_id)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                return False
            
            if success:
                # 验证成功，增加健康度
                session.health_score = min(100, session.health_score + 5)
                session.last_verified_at = datetime.now()
                session.last_used_at = datetime.now()
                logger.info(f"会话验证成功，健康度+5: {session_id}")
            else:
                # 验证失败，降低健康度
                session.health_score = max(0, session.health_score - 20)
                if session.health_score < 60:
                    session.status = "expired"
                logger.warning(f"会话验证失败，健康度-20: {session_id}")
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"验证会话失败 {session_id}: {e}")
            await self.db.rollback()
            return False

    async def delete_session(self, session_id: int) -> bool:
        """
        删除会话
        :param session_id: 会话ID
        :return: 是否删除成功
        """
        try:
            stmt = select(PlatformSession).where(PlatformSession.id == session_id)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                return False
            
            await self.db.delete(session)
            await self.db.commit()
            logger.info(f"删除会话成功: {session_id}")
            return True
        except Exception as e:
            logger.error(f"删除会话失败 {session_id}: {e}")
            await self.db.rollback()
            return False
