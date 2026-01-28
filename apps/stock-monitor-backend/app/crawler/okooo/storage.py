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
        match_id = match_data.get("match_id")
        home_team = match_data.get("home_team")
        away_team = match_data.get("away_team")
        match_type = match_data.get("match_type", "jczq")  # Default to jczq
        
        if not home_team or not away_team:
            logger.warning(f"Skipping save_basic_match_info due to missing teams: {match_data}")
            return False
            
        # Try to parse match_date
        match_time = match_data.get("match_time", "")
        match_timestamp = None
        
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
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        match_timestamp = int(dt.timestamp())
            except Exception:
                pass

        try:
            async with self.db_manager.get_session() as session:
                existing_match = None
                
                # 1. Try to find by match_id if available
                if match_id:
                    stmt = select(OkoooMatch).where(OkoooMatch.match_id == match_id)
                    result = await session.execute(stmt)
                    existing_match = result.scalar_one_or_none()
                
                # 2. If not found by ID, try by teams (fallback)
                if not existing_match:
                    stmt = select(OkoooMatch).where(
                        OkoooMatch.home_team == home_team,
                        OkoooMatch.away_team == away_team
                    ).limit(1)
                    result = await session.execute(stmt)
                    existing_match = result.scalars().first()

                if existing_match:
                    # Update if needed
                    if match_data.get("league"):
                        existing_match.league_name = match_data.get("league")
                    if match_timestamp:
                        existing_match.match_date = match_timestamp
                    
                    # Update match_id and type if missing or changed
                    if match_id:
                        existing_match.match_id = match_id
                    if match_type:
                        existing_match.match_type = match_type
                    if match_data.get("match_no"):
                        existing_match.match_no = match_data.get("match_no")
                            
                else:
                    # Create new
                    logger.info(f"Creating new match from list: {home_team} vs {away_team} (ID: {match_id})")
                    match = OkoooMatch(
                        league_name=match_data.get("league"),
                        match_no=match_data.get("match_no"),
                        match_id=match_id if match_id else "",
                        match_type=match_type,
                        home_team=home_team,
                        away_team=away_team,
                        match_time_text=match_data.get("match_time"),
                        match_date=match_timestamp,
                        history_data="{}"  # Initialize with empty JSON string
                    )
                    session.add(match)
                
                await session.commit()
                
            return True
        except Exception as e:
            logger.error(f"Failed to save basic match info: {e}")
            return False

    async def save_match_json(self, match_id: str, data: Dict[str, Any]) -> bool:
        """
        保存比赛数据为JSON文件，格式匹配 1314249.json
        :param match_id: 比赛ID
        :param data: 解析后的数据字典
        """
        try:
            # 确保输出目录存在
            # 路径: data/okooo/processed_samples/[match_id].json
            base_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "okooo", "processed_samples"))
            os.makedirs(base_dir, exist_ok=True)
            
            file_path = os.path.join(base_dir, f"{match_id}.json")
            
            existing_data = {}
            import aiofiles
            
            # 1. Try to read existing file
            if os.path.exists(file_path):
                try:
                    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                        content = await f.read()
                        if content:
                            existing_data = json.loads(content)
                except Exception as e:
                    logger.warning(f"Failed to read existing JSON {file_path}: {e}")
            
            # 2. Merge data
            # Simple update for top-level keys
            existing_data.update(data)
            
            # 3. Write back
            async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(existing_data, ensure_ascii=False, indent=2))
                
            logger.info(f"Saved match data to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON for match {match_id}: {e}")
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
        match_id = match_info.get("match_id") or parsed_data.get("match_id")
        
        if not home_team or not away_team:
            logger.warning(f"Missing home/away team in match info for url: {source_url}. Info: {match_info}")
            return False
            
        # Prepare data for new columns
        form_data = {
            "home": parsed_data.get("home_history", []),
            "away": parsed_data.get("away_history", [])
        }
        
        # Extract odds data from history or dedicated field if exists
        # Currently the parser puts euro_odds inside history items
        # But if there's a dedicated odds field in future, we use it
        odds_data = parsed_data.get("odds_data", {})
        exchange_data = parsed_data.get("exchange_data", {})
        
        # history_data: Full parsed data as per requirement
        history_data_str = json.dumps(parsed_data, ensure_ascii=False)
        form_data_str = json.dumps(form_data, ensure_ascii=False)
        odds_data_str = json.dumps(odds_data, ensure_ascii=False) if odds_data else None
        exchange_data_str = json.dumps(exchange_data, ensure_ascii=False) if exchange_data else None
        
        try:
            async with self.db_manager.get_session() as session:
                existing_match = None
                
                # 1. Try to find by match_id
                if match_id:
                    stmt = select(OkoooMatch).where(OkoooMatch.match_id == match_id)
                    result = await session.execute(stmt)
                    existing_match = result.scalar_one_or_none()
                
                # 2. Fallback to teams and time
                if not existing_match:
                    stmt = select(OkoooMatch).where(
                        OkoooMatch.home_team == home_team,
                        OkoooMatch.away_team == away_team,
                        OkoooMatch.match_time_text == match_info.get("score_text")
                    )
                    result = await session.execute(stmt)
                    existing_match = result.scalar_one_or_none()

                if existing_match:
                    logger.info(f"Updating existing match: {home_team} vs {away_team}")
                    existing_match.league_name = match_info.get("league")
                    
                    # Update new columns
                    existing_match.history_data = history_data_str
                    existing_match.form_data = form_data_str
                    if odds_data_str:
                        existing_match.odds_data = odds_data_str
                    if exchange_data_str:
                        existing_match.exchange_data = exchange_data_str
                        
                    # Update data and analysis if available
                    if "data" in parsed_data:
                        existing_match.data = parsed_data["data"]
                    if "analysis" in parsed_data:
                        existing_match.analysis = parsed_data["analysis"]
                        
                else:
                    logger.info(f"Creating new match: {home_team} vs {away_team}")
                    
                    # Try to parse match_date for new match
                    match_timestamp = None
                    match_time = match_info.get("score_text", "")
                    # Try to extract date from score_text or other fields if possible
                    # But usually detail page might not have standard date format
                    
                    match = OkoooMatch(
                        league_name=match_info.get("league"),
                        match_id=match_id if match_id else "",
                        match_no=parsed_data.get("match_no"),
                        match_type=parsed_data.get("match_type", "jczq"),
                        home_team=home_team,
                        away_team=away_team,
                        match_time_text=match_info.get("score_text"),
                        match_date=match_timestamp,
                        history_data=history_data_str,
                        form_data=form_data_str,
                        odds_data=odds_data_str,
                        exchange_data=exchange_data_str,
                        data=parsed_data.get("data"),
                        analysis=parsed_data.get("analysis")
                    )
                    session.add(match)
                
                await session.commit()
                
            if source_url:
                await self.mark_as_processed(source_url)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save match data: {e}")
            return False
