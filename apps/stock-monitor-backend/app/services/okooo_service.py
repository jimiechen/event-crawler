# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc, update, delete
from app.models.okooo_match import OkoooMatch
from app.database import db_manager
from app.services.redis_cache_service import RedisCacheService
from app.crawler.okooo.scheduler import OkoooScheduler
from app.services.task_executor import manager  # WebSocket manager
from app.services.sse_service import sse_service  # SSE Service

logger = logging.getLogger(__name__)

class OkoooService:
    """
    Okooo爬虫服务
    管理OkoooScheduler的生命周期，处理API请求和日志推送
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OkoooService, cls).__new__(cls)
            cls._instance.scheduler = None
            cls._instance.is_running = False
            cls._instance._crawl_task = None
            cls._instance.repair_tasks = []
            cls._instance.redis_service = RedisCacheService()
        return cls._instance

    def __init__(self):
        # 已经在__new__中初始化，避免重复初始化
        pass

    async def get_crawl_entry_points(self) -> List[Dict[str, Any]]:
        """
        从数据库获取爬虫入口配置
        select name, url, parent_id, is_active FROM test_pages WHERE parent_id is null and platform = 'okooo' and is_active = 1
        """
        try:
            from sqlalchemy import text
            async with db_manager.get_session() as session:
                stmt = text("select name, url, parent_id, is_active FROM test_pages WHERE parent_id is null and platform = 'okooo' and is_active = 1")
                result = await session.execute(stmt)
                rows = result.fetchall()
                
                entry_points = []
                for row in rows:
                    entry_points.append({
                        "name": row[0],
                        "url": row[1],
                        "parent_id": row[2],
                        "is_active": row[3]
                    })
                return entry_points
        except Exception as e:
            logger.error(f"Error getting crawl entry points: {e}")
            return []

    async def get_db_matches(self, date_str: Optional[str] = None, match_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从数据库获取比赛列表
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(OkoooMatch)
                
                if date_str:
                    stmt = stmt.where(OkoooMatch.match_date == date_str)
                
                if match_type:
                    stmt = stmt.where(OkoooMatch.match_type == match_type)
                
                # Order by match time or ID
                stmt = stmt.order_by(desc(OkoooMatch.match_date), desc(OkoooMatch.id))
                
                result = await session.execute(stmt)
                matches = result.scalars().all()
                
                return [{
                    "id": m.id,
                    "match_id": m.match_id,
                    "match_type": m.match_type,
                    "league": m.league_name,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "match_time": m.match_time_text,
                    "match_date": m.match_date,
                    "history_data": m.history_data,
                    "is_caw": m.is_caw if hasattr(m, 'is_caw') else 1
                } for m in matches]
        except Exception as e:
            logger.error(f"Error getting db matches: {e}")
            return []

    async def update_match_caw_status(self, match_id: int, is_caw: int) -> bool:
        """
        更新比赛爬取状态
        """
        try:
            async with db_manager.get_session() as session:
                stmt = update(OkoooMatch).where(OkoooMatch.id == match_id).values(is_caw=is_caw)
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating match caw status: {e}")
            return False

    async def delete_match(self, match_id: int) -> bool:
        """
        删除比赛
        """
        try:
            async with db_manager.get_session() as session:
                stmt = delete(OkoooMatch).where(OkoooMatch.id == match_id)
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting match: {e}")
            return False


    async def get_matches_dates(self) -> List[str]:
        """
        获取所有有比赛的日期
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(OkoooMatch.match_date).distinct().where(OkoooMatch.match_date.isnot(None)).order_by(desc(OkoooMatch.match_date))
                result = await session.execute(stmt)
                dates = result.scalars().all()
                
                # Filter valid dates and deduplicate (though distinct should handle it)
                valid_dates = []
                seen = set()
                for d in dates:
                    if d and d not in seen:
                        valid_dates.append(d)
                        seen.add(d)
                
                return valid_dates
        except Exception as e:
            logger.error(f"Error getting match dates: {e}")
            return []

    async def get_scheduler(self) -> OkoooScheduler:
        """获取或初始化调度器"""
        if self.scheduler is None:
            redis_service = RedisCacheService()
            # 注意：db_manager应该是已经初始化的全局实例
            self.scheduler = OkoooScheduler(db_manager, redis_service)
            self.scheduler.set_callbacks(
                log_cb=self._on_log,
                progress_cb=self._on_progress,
                match_list_cb=self._on_match_list
            )
        return self.scheduler

    async def _on_log(self, level: str, message: str):
        """日志回调"""
        log_data = {
            "type": "okooo_log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            await manager.broadcast(log_data)
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")
        try:
            await sse_service.broadcast("okooo_log", log_data)
        except Exception as e:
            logger.debug(f"SSE broadcast failed: {e}")

    async def _on_progress(self, processed: int, total: int):
        """进度回调"""
        progress_data = {
            "type": "okooo_progress",
            "processed": processed,
            "total": total,
            "percentage": round(processed / total * 100, 2) if total > 0 else 0
        }
        try:
            await manager.broadcast(progress_data)
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")
        try:
            await sse_service.broadcast("okooo_progress", progress_data)
        except Exception as e:
            logger.debug(f"SSE broadcast failed: {e}")

    async def _on_match_list(self, matches: list):
        """比赛列表回调"""
        data = {
            "type": "okooo_matches",
            "matches": matches
        }
        try:
            await manager.broadcast(data)
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")
        try:
            await sse_service.broadcast("okooo_matches", data)
        except Exception as e:
            logger.debug(f"SSE broadcast failed: {e}")

    def _replace_match_id(self, template: str, match_id: str) -> str:
        """替换 URL 模板中的 match_id"""
        import re
        # 优先处理占位符
        if "{match_id}" in template or "{id}" in template:
            return template.replace("{match_id}", str(match_id)).replace("{id}", str(match_id))
        
        # 其次处理已存在的 MatchID 参数
        if "MatchID=" in template:
            template = re.sub(r'MatchID=\d+', f'MatchID={match_id}', template)

        # 处理 mid 参数 (用于 change.php 等)
        if "mid=" in template:
            template = re.sub(r'mid=\d+', f'mid={match_id}', template)
            
        return template

    async def repair_daily_data(self, date_str: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        检查指定日期的比赛数据完整性，并重新爬取缺失或无效的比赛
        :param date_str: 日期字符串
        :param dry_run: 如果为True，只检查不触发后端爬取
        """
        import os
        
        await self._on_log("INFO", f"Starting repair check for date: {date_str} (Dry Run: {dry_run})")
        
        # 1. Get matches from DB
        matches = await self.get_db_matches(date_str)
        if not matches:
             await self._on_log("WARNING", f"No matches found in DB for date: {date_str}")
             return {"total": 0, "repaired": 0, "message": "No matches found for date", "ids": []}
             
        await self._on_log("INFO", f"Found {len(matches)} matches in DB for {date_str}. Checking files...")
             
        # 2. Check files
        base_dir = os.path.join(os.getcwd(), "data", "okooo", "matches", date_str)
        ids_to_crawl = []
        repair_details = []
        match_missing_types = {}  # 记录每个比赛缺失的文件类型 {match_id: [type_keys]}
        
        # Expected file prefixes based on test_pages table configuration
        # 根据test_pages表配置定义检查规则（8个类型）
        expected_checks = {
            "history": {"name": "澳客历史", "prefixes": ["history_"], "required": True},
            "exchanges": {"name": "澳客盈亏", "prefixes": ["exchanges_"], "required": True},
            "form": {"name": "澳客阵容", "prefixes": ["form_"], "required": True},
            "handicap": {"name": "澳客亚盘", "prefixes": ["handicap_"], "required": True},
            "odds": {"name": "澳客欧赔", "prefixes": ["odds_"], "required": True},
            "game": {"name": "澳客积分", "prefixes": ["game_"], "required": True},
            "macao_change": {"name": "澳客澳门亚盘变化", "prefixes": ["macao_change_"], "required": True},
            "bifa_change": {"name": "澳客必发指数变化", "prefixes": ["bifa_change_"], "required": True},
        }
        
        for i, m in enumerate(matches):
            mid = m.get('match_id')
            if not mid: continue
            
            # Skip if crawling is disabled for this match
            if m.get('is_caw') == 0:
                await self._on_log("INFO", f"Match {mid}: Crawling disabled (is_caw=0), skipping")
                continue
            
            if i % 10 == 0:
                 # Periodic progress log
                 await self._on_log("INFO", f"Checked {i}/{len(matches)} matches...")
            
            match_dir = os.path.join(base_dir, mid)
            
            # If directory doesn't exist, definitely re-crawl
            if not os.path.exists(match_dir):
                ids_to_crawl.append(mid)
                match_missing_types[mid] = list(expected_checks.keys())  # 所有类型都缺失
                repair_details.append({"id": mid, "reason": "目录缺失", "missing_files": [v["name"] for v in expected_checks.values()]})
                await self._on_log("WARNING", f"Match {mid}: Directory missing")
                continue
                
            # Get all HTML files
            files = os.listdir(match_dir)
            html_files = [f for f in files if f.endswith('.html')]
            
            # Check each expected file prefix exists and is valid
            missing_names = []
            missing_types = []  # 记录缺失的类型key
            invalid_files = []
            
            for key, check in expected_checks.items():
                name = check["name"]
                prefixes = check["prefixes"]
                
                # Find files matching any of the prefixes
                matching_files = [f for f in html_files if any(f.startswith(p) for p in prefixes)]
                
                # Special handling to avoid overlap:
                # 'handicap' category should NOT match 'handicap-change' files
                if key == "handicap":
                    matching_files = [f for f in matching_files if not f.startswith("handicap-change")]
                
                if not matching_files:
                    missing_names.append(name)
                    missing_types.append(key)  # 记录缺失的类型
                else:
                    # Check file size for all matching files
                    for f in matching_files:
                        fpath = os.path.join(match_dir, f)
                        if os.path.getsize(fpath) < 2048:  # 2KB
                            invalid_files.append(f"{name}({f})")
                            if key not in missing_types:
                                missing_types.append(key)  # 文件无效也需要重新爬取
            
            if missing_names or invalid_files:
                ids_to_crawl.append(mid)
                match_missing_types[mid] = missing_types  # 保存该比赛缺失的类型
                reasons = []
                if missing_names:
                    reasons.append(f"缺失: {', '.join(missing_names)}")
                if invalid_files:
                    reasons.append(f"无效: {', '.join(invalid_files)}")
                repair_details.append({
                    "id": mid,
                    "reason": "; ".join(reasons),
                    "file_count": f"{len(html_files)}/{len(expected_checks)}"
                })
                await self._on_log("WARNING", f"Match {mid}: {'; '.join(reasons)}")
                # 发送SSE日志到浏览器插件
                await sse_service.broadcast("okooo_log", {
                    "level": "WARNING",
                    "message": f"⚠️ Match {mid}: {'; '.join(reasons)}",
                    "match_id": mid,
                    "timestamp": datetime.now().isoformat()
                })
                continue

        # 3. Start crawling if needed and not dry_run
        if ids_to_crawl and not dry_run:
            # 生成任务队列 - 根据每个比赛缺失的具体文件类型生成任务
            tasks = []
            for match_id in ids_to_crawl:
                missing_types = match_missing_types.get(match_id, [])
                
                for type_key in missing_types:
                    task = self._generate_repair_task(match_id, type_key)
                    if task:
                        tasks.append(task)
            
            # 保存任务队列
            self.repair_tasks = tasks
            self._save_repair_tasks_to_redis(tasks)
            
            # 保存任务队列
            self.repair_tasks = tasks
            self._save_repair_tasks_to_redis(tasks)
            
            await self._on_log("INFO", f"Generated {len(tasks)} repair tasks for {len(ids_to_crawl)} matches.")
            
            # 通知前端有修复任务待执行
            await sse_service.broadcast("okooo_repair_tasks_ready", {
                'date': date_str,
                'total_matches': len(ids_to_crawl),
                'total_tasks': len(tasks),
                'message': f'有 {len(ids_to_crawl)} 个比赛需要修复，共 {len(tasks)} 个页面待爬取'
            })
            
        await self._on_log("INFO", f"Repair check complete. Found {len(ids_to_crawl)} matches to repair.")
            
        return {
            "total_checked": len(matches), 
            "repairing_count": len(ids_to_crawl), 
            "ids": ids_to_crawl,
            "repair_details": repair_details,
            "message": f"Found {len(ids_to_crawl)} matches to repair out of {len(matches)}"
        }

    def _generate_repair_task(self, match_id: str, type_key: str) -> Optional[Dict[str, Any]]:
        """
        根据文件类型生成修复任务
        
        Args:
            match_id: 比赛ID
            type_key: 文件类型key (history, exchanges, form, handicap, odds, game, macao_change, bifa_change)
            
        Returns:
            任务字典或None
        """
        # URL模板映射 - 根据test_pages表配置（8个类型）
        url_templates = {
            "history": f"https://m.okooo.com/match/history.php?MatchID={match_id}&from=%2Fjczq%2F",
            "exchanges": f"https://m.okooo.com/match/exchanges.php?MatchID={match_id}&from=%2Fjczq%2F",
            "form": f"https://m.okooo.com/match/form.php?MatchID={match_id}&from=%2Fjczq%2F",
            "handicap": f"https://m.okooo.com/match/handicap.php?MatchID={match_id}&from=%2Fjczq%2F",
            "odds": f"https://m.okooo.com/match/odds.php?MatchID={match_id}&from=%2Fjczq%2F",
            "game": f"https://m.okooo.com/match/game.php?MatchID={match_id}&from=%2Fjczq%2F",
            "macao_change": f"https://m.okooo.com/match/change.php?mid={match_id}&pid=84&Type=Handicap",
            "bifa_change": f"https://m.okooo.com/match/change.php?mid={match_id}&pid=19&Type=odds",
        }
        
        # page_type映射
        page_type_map = {
            "history": "mobile_history",
            "exchanges": "mobile_exchanges",
            "form": "mobile_form",
            "handicap": "mobile_handicap",
            "odds": "mobile_odds",
            "game": "mobile_game",
            "macao_change": "mobile_macao_change",
            "bifa_change": "mobile_bifa_change",
        }
        
        # filename_prefix映射
        prefix_map = {
            "history": "history",
            "exchanges": "exchanges",
            "form": "form",
            "handicap": "handicap",
            "odds": "odds",
            "game": "game",
            "macao_change": "macao_change",
            "bifa_change": "bifa_change",
        }
        
        if type_key not in url_templates:
            logger.warning(f"Unknown repair type: {type_key} for match {match_id}")
            return None
            
        return {
            'match_id': match_id,
            'url': url_templates[type_key],
            'page_type': page_type_map.get(type_key, 'unknown'),
            'filename_prefix': prefix_map.get(type_key, 'unknown')
        }

    def _save_repair_tasks_to_redis(self, tasks: List[Dict[str, Any]]):
        """保存修复任务到Redis"""
        import json
        try:
            # key: okooo:repair_tasks
            # expire: 24h
            self.redis_service.client.set("okooo:repair_tasks", json.dumps(tasks), ex=86400)
        except Exception as e:
            logger.error(f"Error saving repair tasks to redis: {e}")

    async def get_repair_tasks(self) -> List[Dict[str, Any]]:
        """
        获取当前的修复任务列表
        优先从内存获取，如果没有则从Redis获取
        """
        # 1. 先从内存获取
        if hasattr(self, 'repair_tasks') and self.repair_tasks:
            return self.repair_tasks
        
        # 2. 从Redis获取
        try:
            import json
            tasks_json = self.redis_service.client.get("okooo:repair_tasks")
            if tasks_json:
                return json.loads(tasks_json)
        except Exception as e:
            logger.error(f"Error getting repair tasks from redis: {e}")
        
        # 3. 返回空列表
        return []

    async def check_files_exist(self, tasks: List[Dict[str, Any]], date_str: str) -> List[Dict[str, Any]]:
        """
        批量检查文件是否存在且有效
        """
        import os
        
        results = []
        base_dir = os.path.join(os.getcwd(), "data", "okooo", "matches", date_str)
        
        for task in tasks:
            match_id = task.get('match_id')
            page_type = task.get('page_type')
            filename_prefix = task.get('filename_prefix')
            
            if not match_id:
                continue
            
            # 生成文件名 - 优先使用 filename_prefix
            if filename_prefix:
                filename = f"{filename_prefix}_{match_id}.html"
            else:
                filename = self._get_filename_by_type(page_type, match_id)
            
            # 检查文件是否存在
            match_dir = os.path.join(base_dir, match_id)
            save_path = os.path.join(match_dir, filename)
            
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                if file_size >= 2048:
                    results.append({
                        "match_id": match_id,
                        "page_type": page_type,
                        "filename": filename,
                        "exists": True,
                        "size": file_size,
                        "skip": True
                    })
                else:
                    results.append({
                        "match_id": match_id,
                        "page_type": page_type,
                        "filename": filename,
                        "exists": True,
                        "size": file_size,
                        "skip": False,
                        "reason": "文件太小"
                    })
            else:
                results.append({
                    "match_id": match_id,
                    "page_type": page_type,
                    "filename": filename,
                    "exists": False,
                    "skip": False
                })
        
        return results

    async def check_single_file_exists(self, match_id: str, page_type: str) -> bool:
        """
        检查单个文件是否已存在且有效
        用于爬虫防重复机制
        """
        import os
        
        try:
            # 获取今天的日期
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            # 生成文件名
            filename = self._get_filename_by_type(page_type, match_id)
            
            # 构建文件路径
            base_dir = os.path.join(os.getcwd(), "data", "okooo", "matches", date_str)
            match_dir = os.path.join(base_dir, match_id)
            save_path = os.path.join(match_dir, filename)
            
            # 检查文件是否存在且大小 >= 2KB
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                if file_size >= 2048:
                    logger.info(f"[OkoooCheck] 文件已存在: {save_path} ({file_size} bytes)")
                    return True
                else:
                    logger.warning(f"[OkoooCheck] 文件存在但太小: {save_path} ({file_size} bytes)")
                    return False
            
            # 也检查 processed 目录
            processed_dir = os.path.join(os.getcwd(), "data", "okooo", "processed", date_str)
            processed_path = os.path.join(processed_dir, f"{match_id}.json")
            
            if os.path.exists(processed_path):
                file_size = os.path.getsize(processed_path)
                if file_size >= 1024:  # processed 文件可以小一些
                    logger.info(f"[OkoooCheck] processed文件已存在: {processed_path}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"[OkoooCheck] 检查文件存在性失败: {e}")
            return False

    async def start_crawl(self, start_id: int, end_id: int) -> bool:
        """启动爬虫任务"""
        if self.is_running:
            logger.warning("Okooo crawler is already running")
            return False

        scheduler = await self.get_scheduler()
        self.is_running = True
        
        # 创建后台任务
        self._crawl_task = asyncio.create_task(self._run_crawl(scheduler, start_id, end_id))
        return True

    async def fetch_match_lists(self, headless: bool = True, use_cache: bool = False, use_proxy: bool = False) -> list:
        """获取比赛列表"""
        scheduler = await self.get_scheduler()
        
        # Configure
        storage_path = "okooo_session.json" if use_cache else None
        
        # 强制配置更新，确保单例模式下的配置一致性
        await scheduler.configure(headless=headless, storage_state_path=storage_path, use_proxy=use_proxy)
        
        return await scheduler.fetch_match_lists()

    async def start_crawl_lists(self, headless: bool = True, use_cache: bool = False, use_proxy: bool = False) -> bool:
        """启动列表爬虫任务"""
        if self.is_running:
            logger.warning("Okooo crawler is already running")
            return False

        scheduler = await self.get_scheduler()
        
        # Configure
        storage_path = "okooo_session.json" if use_cache else None
        await scheduler.configure(headless=headless, storage_state_path=storage_path, use_proxy=use_proxy)
        
        self.is_running = True
        
        # 创建后台任务
        self._crawl_task = asyncio.create_task(self._run_crawl_lists(scheduler))
        return True

    async def start_crawl_ids(self, match_ids: list, headless: bool = True, use_cache: bool = False, force: bool = False, use_proxy: bool = False, date_str: Optional[str] = None) -> bool:
        """启动指定ID列表爬虫任务"""
        if self.is_running:
            logger.warning("Okooo crawler is already running")
            return False

        # Filter out disabled matches
        try:
            async with db_manager.get_session() as session:
                # Ensure match_ids are integers for DB query
                valid_int_ids = []
                for mid in match_ids:
                    try:
                        valid_int_ids.append(int(mid))
                    except (ValueError, TypeError):
                        pass
                
                if valid_int_ids:
                    stmt = select(OkoooMatch.match_id).where(OkoooMatch.match_id.in_(valid_int_ids)).where(OkoooMatch.is_caw == 0)
                    result = await session.execute(stmt)
                    disabled_ids = result.scalars().all()
                    
                    if disabled_ids:
                        disabled_set = set(str(id) for id in disabled_ids)
                        original_count = len(match_ids)
                        match_ids = [mid for mid in match_ids if str(mid) not in disabled_set]
                        logger.info(f"Filtered out {original_count - len(match_ids)} disabled matches: {disabled_set}")
                        
                        if not match_ids:
                            logger.warning("No valid matches to crawl after filtering disabled ones")
                            return False
        except Exception as e:
            logger.error(f"Error filtering disabled matches: {e}")
            # Continue with original list if check fails, or return False? 
            # Safer to continue or fail? Let's log and continue to avoid blocking due to DB error.

        scheduler = await self.get_scheduler()
        
        # Configure
        storage_path = "okooo_session.json" if use_cache else None
        await scheduler.configure(headless=headless, storage_state_path=storage_path, use_proxy=use_proxy)
        
        self.is_running = True
        
        # 创建后台任务
        self._crawl_task = asyncio.create_task(self._run_crawl_ids(scheduler, match_ids, force, date_str))
        return True

    async def _run_crawl_ids(self, scheduler: OkoooScheduler, match_ids: list, force: bool = False, date_str: Optional[str] = None):
        """执行ID列表爬虫任务的包装器"""
        try:
            await scheduler.crawl_ids(match_ids, force=force, date_str=date_str)
        except Exception as e:
            logger.error(f"Crawl ids task error: {e}")
            await self._on_log("ERROR", f"Crawl ids task crashed: {e}")
        finally:
            self.is_running = False
            await self._on_log("INFO", "Crawl ids task ended")
            await manager.broadcast({
                "type": "okooo_status",
                "is_running": False
            })
            await sse_service.broadcast("okooo_status", {
                "type": "okooo_status",
                "is_running": False
            })

    async def _run_crawl_lists(self, scheduler: OkoooScheduler):
        """执行列表爬虫任务的包装器"""
        try:
            await scheduler.crawl_match_lists()
        except Exception as e:
            logger.error(f"Crawl lists task error: {e}")
            await self._on_log("ERROR", f"Crawl lists task crashed: {e}")
        finally:
            self.is_running = False
            await self._on_log("INFO", "Crawl lists task ended")
            await manager.broadcast({
                "type": "okooo_status",
                "is_running": False
            })
            await sse_service.broadcast("okooo_status", {
                "type": "okooo_status",
                "is_running": False
            })

    async def _run_crawl(self, scheduler: OkoooScheduler, start_id: int, end_id: int):
        """执行爬虫任务的包装器"""
        try:
            await scheduler.crawl_range(start_id, end_id)
        except Exception as e:
            logger.error(f"Crawl task error: {e}")
            await self._on_log("ERROR", f"Crawl task crashed: {e}")
        finally:
            self.is_running = False
            await self._on_log("INFO", "Crawl task ended")
            # 发送最终状态
            await manager.broadcast({
                "type": "okooo_status",
                "is_running": False
            })
            await sse_service.broadcast("okooo_status", {
                "type": "okooo_status",
                "is_running": False
            })

    async def stop_crawl(self):
        """停止爬虫任务"""
        if self.scheduler and self.is_running:
            self.scheduler.stop()
            await self._on_log("WARNING", "Stopping crawler...")
            
            # Cancel the task to unblock any waits (like queue.join)
            if self._crawl_task and not self._crawl_task.done():
                self._crawl_task.cancel()
                try:
                    await self._crawl_task
                except asyncio.CancelledError:
                    await self._on_log("INFO", "Crawler task cancelled")
                except Exception as e:
                    await self._on_log("ERROR", f"Error waiting for crawler task: {e}")
            
            self.is_running = False

    async def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        stats = self.scheduler.stats if self.scheduler else {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        return {
            "is_running": self.is_running,
            "stats": stats
        }

    async def capture_history_match(
        self,
        url: str,
        match_id: str,
        parent_match_id: str = None,
        source: str = "okooo_crawler"
    ) -> Dict[str, Any]:
        """
        捕获并保存历史记录比赛页面
        """
        import httpx
        import os
        import aiofiles

        try:
            # 下载页面 HTML
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                html_content = response.text

            # 构建保存路径
            date_str = datetime.now().strftime('%Y-%m-%d')

            # 统一保存到 matches 目录
            save_dir = os.path.abspath(os.path.join(
                os.getcwd(), "data", "okooo", "matches", date_str, match_id
            ))

            os.makedirs(save_dir, exist_ok=True)

            save_path = os.path.join(save_dir, "history.html")

            # 保存 HTML
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)

            logger.info(f"[OkoooHistory] 保存成功: {save_path}")
            await self._on_log("INFO", f"Saved history file: history.html")

            # 发送 SSE 通知
            await sse_service.broadcast("okooo_file_saved", {
                "match_id": match_id,
                "parent_match_id": parent_match_id,
                "page_type": "history",
                "filename": "history.html",
                "path": save_path
            })

            return {
                "success": True,
                "match_id": match_id,
                "parent_match_id": parent_match_id,
                "url": url,
                "source": source,
                "save_path": save_path,
                "content_length": len(html_content),
                "saved_at": date_str
            }

        except Exception as e:
            logger.error(f"[OkoooHistory] 保存失败 {match_id}: {e}")
            raise

    async def save_list_html(
        self,
        html: str,
        url: str,
        captured_at: str,
        date: str
    ) -> Dict[str, Any]:
        """
        保存比赛列表 HTML 页面
        保存到 data/okooo/list/[date]/
        """
        import os
        import aiofiles

        try:
            # 构建保存路径
            save_dir = os.path.abspath(os.path.join(
                os.getcwd(), "data", "okooo", "list", date
            ))
            os.makedirs(save_dir, exist_ok=True)

            # 文件名使用时间戳
            timestamp = captured_at.replace(':', '-').replace('T', '_').split('.')[0]
            save_path = os.path.join(save_dir, f"match_list_{timestamp}.html")

            # 保存 HTML 文件
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(html)

            logger.info(f"[OkoooList] 保存成功: {save_path}")
            await self._on_log("INFO", f"Saved list file: {save_path}")
            
            # 解析并入库
            from app.crawler.okooo.parser import OkoooParser
            
            if "m.okooo.com" in url:
                matches = OkoooParser.parse_mobile_match_list(html)
            else:
                matches = OkoooParser.parse_match_list(html)
            
            # Determine match_type from URL
            match_type = "jczq" # default
            if "bjdc" in url:
                match_type = "bjdc"
            elif "sfc" in url:
                match_type = "sfc"
            elif "jczq" in url:
                match_type = "jczq"
            
            scheduler = await self.get_scheduler()
            saved_count = 0
            for match in matches:
                # Add match_type
                match["match_type"] = match_type
                
                # 将 match_id 和 date 传入
                success = await scheduler.storage.save_basic_match_info(match, date_str=date)
                if success:
                    saved_count += 1
            
            logger.info(f"[OkoooList] 解析并入库成功: {saved_count} 条比赛数据")

            return {
                "success": True,
                "url": url,
                "save_path": save_path,
                "html_size": len(html),
                "captured_at": captured_at,
                "date": date,
                "saved_matches": saved_count
            }

        except Exception as e:
            logger.error(f"[OkoooList] 保存失败: {e}")
            raise

    def _validate_html_content(self, html: str):
        """验证 HTML 内容有效性"""
        if not html or len(html) < 500:
            raise ValueError("页面内容为空或过短")
        if "验证码" in html or "访问过于频繁" in html or "security check" in html.lower():
            raise ValueError("页面包含验证码或访问限制")
        if "页面找不到了" in html or "404/search_children.js" in html:
            raise ValueError("页面为404错误页")

    def _get_filename_by_type(self, page_type: Optional[str], match_id: str, pid: Optional[str] = None) -> str:
        """根据页面类型生成文件名"""
        filename_map = {
            # 中文类型（前端传入）- 根据test_pages表配置（8个类型）
            "澳客历史": "history",
            "澳客盈亏": "exchanges",
            "澳客阵容": "form",
            "澳客亚盘": "handicap",
            "澳客欧赔": "odds",
            "澳客积分": "game",
            "澳客澳门亚盘变化": "macao_change",
            "澳客必发指数变化": "bifa_change",
            # 英文类型（数据库/Redis存储）
            "mobile_history": "history",
            "mobile_exchanges": "exchanges",
            "mobile_form": "form",
            "mobile_handicap": "handicap",
            "mobile_odds": "odds",
            "mobile_game": "game",
            "mobile_macao_change": "macao_change",
            "mobile_bifa_change": "bifa_change",
        }
        prefix = filename_map.get(page_type, "index") if page_type else "index"

        return f"{prefix}_{match_id}.html"

    async def save_match_html(
        self,
        html: str,
        url: str,
        match_id: str,
        captured_at: str,
        date: str,
        page_type: Optional[str] = None,
        pid: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        保存比赛详情页面 HTML
        保存到 data/okooo/matches/[date]/[match_id]/
        如果文件已存在且有效，则跳过（除非force=True）
        """
        import os
        import aiofiles

        try:
            # 验证内容
            self._validate_html_content(html)

            # 构建保存路径
            save_dir = os.path.abspath(os.path.join(
                os.getcwd(), "data", "okooo", "matches", date, match_id
            ))
            os.makedirs(save_dir, exist_ok=True)

            # 生成文件名
            filename = self._get_filename_by_type(page_type, match_id, pid)
            save_path = os.path.join(save_dir, filename)

            # 检查文件是否已存在且有效（大小>=2KB）
            if not force and os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                if file_size >= 2048:  # 2KB
                    logger.info(f"[OkoooMatch] 文件已存在且有效，跳过: {save_path} ({file_size} bytes)")
                    await self._on_log("INFO", f"Skipping existing file: {filename} ({file_size} bytes)")
                    # 发送SSE日志到浏览器插件
                    await sse_service.broadcast("okooo_log", {
                        "level": "INFO",
                        "message": f"⏭️ 跳过已存在: {filename} ({file_size} bytes)",
                        "match_id": match_id,
                        "page_type": page_type,
                        "timestamp": captured_at
                    })
                    return {
                        "success": True,
                        "match_id": match_id,
                        "url": url,
                        "filename": filename,
                        "save_path": save_path,
                        "skipped": True,
                        "reason": "File already exists and is valid"
                    }
                else:
                    logger.warning(f"[OkoooMatch] 文件存在但无效（太小），重新下载: {save_path} ({file_size} bytes)")
                    # 发送SSE日志到浏览器插件
                    await sse_service.broadcast("okooo_log", {
                        "level": "WARNING",
                        "message": f"🔄 重新下载(文件太小): {filename} ({file_size} bytes)",
                        "match_id": match_id,
                        "page_type": page_type,
                        "timestamp": captured_at
                    })

            # 保存 HTML 文件
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(html)

            file_size = len(html)
            logger.info(f"[OkoooMatch] 保存成功: {save_path} ({file_size} bytes)")
            await self._on_log("INFO", f"Saved match file: {filename} ({file_size} bytes)")

            # 发送SSE日志到浏览器插件
            await sse_service.broadcast("okooo_log", {
                "level": "SUCCESS",
                "message": f"✅ 保存成功: {filename} ({file_size} bytes)",
                "match_id": match_id,
                "page_type": page_type,
                "timestamp": captured_at
            })

            # 发送 SSE 通知
            await sse_service.broadcast("okooo_file_saved", {
                "match_id": match_id,
                "page_type": page_type or "index",
                "filename": filename,
                "path": save_path,
                "size": file_size
            })

            return {
                "success": True,
                "match_id": match_id,
                "url": url,
                "save_path": save_path,
                "html_size": len(html),
                "captured_at": captured_at,
                "date": date,
                "page_type": page_type,
                "skipped": False
            }

        except Exception as e:
            logger.error(f"[OkoooMatch] 保存失败 {match_id}: {e}")
            raise

    async def save_history_html(
        self,
        html: str,
        url: str,
        match_id: str,
        parent_match_id: str,
        captured_at: str,
        date: str,
        page_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存历史记录页面 HTML（由浏览器扩展直接获取 HTML）
        保存到 data/okooo/matches/[date]/[match_id]/
        """
        import os
        import aiofiles

        try:
            # 验证内容
            self._validate_html_content(html)

            # 构建保存路径 (统一到 matches 目录)
            save_dir = os.path.abspath(os.path.join(
                os.getcwd(), "data", "okooo", "matches", date, match_id
            ))
            os.makedirs(save_dir, exist_ok=True)

            # 生成文件名
            # 如果是历史页面，强制使用 history_{match_id}.html (或者根据 page_type)
            # 既然 page_type 传入了 "澳客历史" 等，_get_filename_by_type 会处理
            filename = self._get_filename_by_type(page_type, match_id)
            save_path = os.path.join(save_dir, filename)

            # 保存 HTML 文件
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(html)

            logger.info(f"[OkoooHistory] 保存成功: {save_path}")
            await self._on_log("INFO", f"Saved history file: {filename}")

            # 发送 SSE 通知
            await sse_service.broadcast("okooo_file_saved", {
                "match_id": match_id,
                "page_type": page_type or "history",
                "filename": filename,
                "path": save_path
            })

            return {
                "success": True,
                "match_id": match_id,
                "parent_match_id": parent_match_id,
                "url": url,
                "save_path": save_path,
                "html_size": len(html),
                "captured_at": captured_at,
                "date": date,
                "page_type": page_type
            }

        except Exception as e:
            logger.error(f"[OkoooHistory] 保存失败 {match_id}: {e}")
            raise

    async def save_history_with_tab(
        self,
        html: str,
        url: str,
        match_id: str,
        parent_match_id: str,
        tab_name: str,
        captured_at: str,
        date: str
    ) -> Dict[str, Any]:
        """
        保存历史记录页面 HTML（带 tab 编号和名称）
        保存到 data/okooo/matches/[date]/[match_id]/history_[tab_name].html
        """
        import os
        import re
        import aiofiles

        try:
            # 验证内容
            self._validate_html_content(html)

            # 清理 tab 名称用于文件名（移除特殊字符）
            safe_tab_name = re.sub(r'[<>:"/\\|?*]', '', tab_name).strip()[:20]
            
            # 构建保存路径 (统一到 matches 目录)
            save_dir = os.path.abspath(os.path.join(
                os.getcwd(), "data", "okooo", "matches", date, match_id
            ))
            os.makedirs(save_dir, exist_ok=True)

            # 保存 HTML 文件
            filename = f"history_{safe_tab_name}.html"
            save_path = os.path.join(save_dir, filename)
            
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(html)

            logger.info(f"[OkoooHistory] 保存成功: {save_path}")
            await self._on_log("INFO", f"Saved history tab file: {filename}")

            # 发送 SSE 通知
            await sse_service.broadcast("okooo_file_saved", {
                "match_id": match_id,
                "parent_match_id": parent_match_id,
                "page_type": "history_tab",
                "tab_name": tab_name,
                "filename": filename,
                "path": save_path
            })

            return {
                "success": True,
                "match_id": match_id,
                "parent_match_id": parent_match_id,
                "tab_name": tab_name,
                "url": url,
                "save_path": save_path,
                "html_size": len(html),
                "captured_at": captured_at,
                "date": date
            }

        except Exception as e:
            logger.error(f"[OkoooHistory] 保存失败 {match_id}: {e}")
            raise

    async def query_matches(self, sql: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询获取比赛数据
        """
        from sqlalchemy import text
        from app.database import db_manager

        try:
            async with db_manager.get_session() as session:
                # 添加 LIMIT
                if "limit" not in sql.lower():
                    sql = f"{sql.rstrip(';')} LIMIT {limit}"
                
                result = await session.execute(text(sql))
                # 获取列名
                keys = result.keys()
                rows = result.fetchall()
                
                results = []
                for row in rows:
                    # 将 row 转换为字典
                    row_dict = dict(zip(keys, row))
                    results.append(row_dict)
                
                logger.info(f"[OkoooQuery] 执行 SQL 查询，返回 {len(results)} 条记录")
                return results

        except Exception as e:
            logger.error(f"[OkoooQuery] SQL 查询失败: {e}")
            raise

    async def save_handicap_html(
        self,
        html: str,
        url: str,
        match_id: str,
        captured_at: str,
        date: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        保存让球盘页面 HTML
        统一到 save_match_html 方法，确保文件名格式一致
        """
        try:
            # 调用统一的保存方法
            return await self.save_match_html(
                html=html,
                url=url,
                match_id=match_id,
                captured_at=captured_at,
                date=date,
                page_type="澳客亚盘",
                force=force
            )
        except Exception as e:
            logger.error(f"[OkoooHandicap] 保存失败 {match_id}: {e}")
            raise

# 全局实例
okooo_service = OkoooService()
