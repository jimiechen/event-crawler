# -*- coding: utf-8 -*-
import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy import select
from app.database import DatabaseManager
from app.models.okooo_match import OkoooMatch
from app.services.redis_cache_service import RedisCacheService

logger = logging.getLogger(__name__)

class OkoooStorage:
    """
    Okooo数据存储管理器
    负责将解析后的数据保存到MySQL，并使用Redis进行去重检查
    """
    
    def __init__(self, db_manager: DatabaseManager, redis_service: RedisCacheService):
        self.db_manager = db_manager
        self.redis_service = redis_service
        self.dedup_key_prefix = "okooo:dedup:"

    async def is_duplicate(self, url: str) -> bool:
        """
        检查URL是否已处理
        """
        try:
            return self.redis_service.client.exists(f"{self.dedup_key_prefix}{url}") > 0
        except Exception as e:
            logger.error(f"Redis check failed: {e}")
            return False

    async def mark_as_processed(self, url: str, expire_seconds: int = 86400 * 7):
        """
        标记URL为已处理
        """
        try:
            key = f"{self.dedup_key_prefix}{url}"
            self.redis_service.client.set(key, "1", ex=expire_seconds)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")

    async def save_match_data(self, parsed_data: Dict[str, Any], source_url: str = "") -> bool:
        """
        保存比赛数据到MySQL
        """
        match_info = parsed_data.get("match_info", {})
        if not match_info:
            logger.warning("No match info found to save")
            return False

        try:
            async with self.db_manager.get_session() as session:
                # 简单去重检查：基于 联赛+主队+客队+时间文本
                # 注意：这只是一个示例，实际去重可能需要更严格的逻辑或依赖 source_url
                stmt = select(OkoooMatch).where(
                    OkoooMatch.home_team == match_info.get("home_team"),
                    OkoooMatch.away_team == match_info.get("away_team"),
                    OkoooMatch.match_time_text == match_info.get("score_text")
                )
                result = await session.execute(stmt)
                existing_match = result.scalar_one_or_none()

                if existing_match:
                    logger.info(f"Updating existing match: {match_info.get('home_team')} vs {match_info.get('away_team')}")
                    existing_match.league_name = match_info.get("league")
                    existing_match.history_data = parsed_data
                    # Update other fields if necessary
                else:
                    logger.info(f"Creating new match: {match_info.get('home_team')} vs {match_info.get('away_team')}")
                    match = OkoooMatch(
                        league_name=match_info.get("league"),
                        home_team=match_info.get("home_team"),
                        away_team=match_info.get("away_team"),
                        match_time_text=match_info.get("score_text"),
                        history_data=parsed_data
                    )
                    session.add(match)
                
                # Commit happens automatically on exit of context manager if no exception
                
            if source_url:
                await self.mark_as_processed(source_url)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save match data: {e}")
            return False
