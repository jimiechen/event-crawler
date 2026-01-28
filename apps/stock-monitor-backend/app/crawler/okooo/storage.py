# -*- coding: utf-8 -*-
import logging
import json
import os
from datetime import datetime, date
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

    async def save_html(self, match_id: str, file_name: str, content: str, date_str: Optional[str] = None) -> bool:
        """
        保存HTML文件到磁盘
        :param match_id: 比赛ID
        :param file_name: 文件名
        :param content: 内容
        :param date_str: 日期字符串 (YYYY-MM-DD)，如果提供，将保存到该日期的子目录中
        """
        try:
            # 使用项目根目录下的 data/okooo/batch_html/
            base_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "okooo", "batch_html"))
            
            if date_str:
                match_dir = os.path.join(base_dir, date_str, match_id)
            else:
                match_dir = os.path.join(base_dir, match_id)
                
            os.makedirs(match_dir, exist_ok=True)
            
            file_path = os.path.join(match_dir, file_name)
            
            # 使用同步写入，对于文件I/O，如果在asyncio中会阻塞，可以使用run_in_executor
            # 但这里简单起见直接写入，因为文件不大
            import aiofiles
            async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
                await f.write(content)
                
            logger.info(f"Saved HTML to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save HTML {file_name} for match {match_id}: {e}")
            # Fallback to sync open if aiofiles fails or is not installed
            try:
                if not os.path.exists(match_dir):
                    os.makedirs(match_dir, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e2:
                 logger.error(f"Fallback save failed: {e2}")
            return False

    async def save_basic_match_info(self, match_data: Dict[str, Any]) -> bool:
        """
        保存比赛列表中的基本信息
        """
        home_team = match_data.get("home_team")
        away_team = match_data.get("away_team")
        
        if not home_team or not away_team:
            logger.warning(f"Skipping save_basic_match_info due to missing teams: {match_data}")
            return False
            
        # Try to parse match_date
        match_time = match_data.get("match_time", "")
        match_date = None
        if match_time:
            try:
                # Expect format "MM-DD HH:MM" or similar
                # Append current year if missing
                if "-" in match_time and ":" in match_time:
                    parts = match_time.split(" ")
                    date_part = parts[0]
                    # Assuming MM-DD
                    if len(date_part.split("-")) == 2:
                        current_year = datetime.now().year
                        date_str = f"{current_year}-{date_part}"
                        match_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        try:
            async with self.db_manager.get_session() as session:
                # 尝试根据主客队查找
                stmt = select(OkoooMatch).where(
                    OkoooMatch.home_team == home_team,
                    OkoooMatch.away_team == away_team
                )
                result = await session.execute(stmt)
                existing_match = result.scalar_one_or_none()

                if existing_match:
                    # Update if needed
                    if match_data.get("league"):
                        existing_match.league_name = match_data.get("league")
                    if match_date:
                        existing_match.match_date = match_date
                        
                    # Merge match_id into history_data if present
                    if existing_match.history_data:
                        existing_data = dict(existing_match.history_data)
                    else:
                        existing_data = {}
                    
                    existing_data["match_id"] = match_data.get("match_id")
                    existing_match.history_data = existing_data
                else:
                    # Create new
                    logger.info(f"Creating new match from list: {home_team} vs {away_team}")
                    match = OkoooMatch(
                        league_name=match_data.get("league"),
                        home_team=home_team,
                        away_team=away_team,
                        match_time_text=match_data.get("match_time"),
                        match_date=match_date,
                        history_data={"match_id": match_data.get("match_id")}
                    )
                    session.add(match)
                
            return True
        except Exception as e:
            logger.error(f"Failed to save basic match info: {e}")
            return False

    async def save_match_data(self, parsed_data: Dict[str, Any], source_url: str = "") -> bool:
        """
        保存比赛数据到MySQL
        """
        match_info = parsed_data.get("match_info", {})
        if not match_info:
            logger.warning(f"No match info found to save for url: {source_url}")
            return False

        # Validate required fields
        home_team = match_info.get("home_team")
        away_team = match_info.get("away_team")
        
        if not home_team or not away_team:
            logger.warning(f"Missing home/away team in match info for url: {source_url}. Info: {match_info}")
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
