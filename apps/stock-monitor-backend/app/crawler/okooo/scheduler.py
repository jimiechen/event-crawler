# -*- coding: utf-8 -*-
import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional, Callable, Awaitable, Dict, Any
from asyncio import Queue
from sqlalchemy import select

from app.database import DatabaseManager
from app.services.redis_cache_service import RedisCacheService
from .url_builder import OkoooUrlBuilder, OkoooPageType
from .downloader import OkoooDownloader
from .parser import OkoooParser
from .storage import OkoooStorage

logger = logging.getLogger(__name__)

class OkoooScheduler:
    """
    Okooo爬虫调度器
    负责任务分发、并发控制和断点续传
    """
    
    def __init__(self, 
                 db_manager: DatabaseManager, 
                 redis_service: RedisCacheService,
                 concurrency: int = 1,
                 delay: float = 5.0):
        self.db_manager = db_manager
        self.redis_service = redis_service
        self.concurrency = concurrency
        self.delay = delay # 请求间隔
        
        self.url_builder = OkoooUrlBuilder()
        self.parser = OkoooParser()
        # Downloader将在run时初始化，确保在正确的事件循环中
        self.downloader: Optional[OkoooDownloader] = None
        self.storage: Optional[OkoooStorage] = None
        
        self.queue: Queue = Queue()
        self.active_workers = 0
        self._stop_event = asyncio.Event()
        
        # 配置
        self.headless = True
        self.is_mobile = True  # Default to mobile as per requirement
        self.storage_state_path = None
        
        # 回调函数
        self.log_callback: Optional[Callable[[str, str], Awaitable[None]]] = None
        self.progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None
        self.match_list_callback: Optional[Callable[[List[Dict[str, Any]]], Awaitable[None]]] = None
        
        # 统计
        self.stats = {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

    async def configure(self, headless: bool = True, is_mobile: bool = True, storage_state_path: Optional[str] = None, use_proxy: bool = False):
        """配置爬虫参数"""
        # 如果配置有变化，且downloader已存在，则关闭旧的以便重新初始化
        config_changed = (
            self.headless != headless or 
            self.is_mobile != is_mobile or 
            self.storage_state_path != storage_state_path or
            getattr(self, "use_proxy", False) != use_proxy
        )
        
        self.headless = headless
        self.is_mobile = is_mobile
        self.storage_state_path = storage_state_path
        self.use_proxy = use_proxy
        
        if self.downloader and config_changed:
            await self._log("INFO", "Configuration changed, restarting downloader...")
            try:
                await self.downloader.close()
            except Exception as e:
                logger.error(f"Error closing downloader: {e}")
            self.downloader = None

    def stop(self):
        """停止爬虫"""
        self._stop_event.set()
        # 清空队列中的任务（如果有的话，虽然Queue没有直接清空的方法，但在worker中处理）

    def set_callbacks(self, 
                      log_cb: Optional[Callable[[str, str], Awaitable[None]]] = None,
                      progress_cb: Optional[Callable[[int, int], Awaitable[None]]] = None,
                      match_list_cb: Optional[Callable[[List[Dict[str, Any]]], Awaitable[None]]] = None):
        """设置回调函数"""
        self.log_callback = log_cb
        self.progress_callback = progress_cb
        self.match_list_callback = match_list_cb

    async def _log(self, level: str, message: str):
        """内部日志记录"""
        if level == "INFO":
            logger.info(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
            
        if self.log_callback:
            try:
                await self.log_callback(level, message)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")

    async def _update_progress(self):
        """更新进度"""
        if self.progress_callback:
            try:
                await self.progress_callback(self.stats["processed"], self.stats["total"])
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")

    async def _init_components(self):
        """初始化组件"""
        if not self.downloader:
            # 单例模式下，如果downloader不存在，则创建新的
            # 只有在downloader确实不存在时才创建，避免覆盖已有的单例实例
            # Use local proxy if configured
            proxy_url = "http://127.0.0.1:8118" if getattr(self, "use_proxy", False) else None
            
            self.downloader = OkoooDownloader(
                headless=self.headless,
                is_mobile=self.is_mobile,
                storage_state_path=self.storage_state_path,
                proxy_url=proxy_url
            )
        else:
            # 如果downloader已存在，确保其配置与当前scheduler配置一致
            # 注意：这可能会涉及到downloader内部状态的更新，但目前OkoooDownloader没有提供动态更新配置的方法
            # 且我们希望复用同一个浏览器实例，所以这里不做强制重启，而是依赖configure方法在必要时重启
            pass

        if not self.storage:
            self.storage = OkoooStorage(self.db_manager, self.redis_service)

    async def _worker(self, worker_id: int):
        """工作协程"""
        # await self._log("INFO", f"Worker {worker_id} started")
        while not self._stop_event.is_set():
            try:
                # 获取任务
                try:
                    task = self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    if self._stop_event.is_set():
                        break
                    await asyncio.sleep(0.5)
                    continue

                if task is None: # 结束信号
                    self.queue.task_done()
                    break
                
                # Support tuples with varying lengths
                date_str = None
                force = False
                filename = None
                
                if len(task) == 6:
                    url, match_id, page_type, date_str, force, filename = task
                elif len(task) == 5:
                    url, match_id, page_type, date_str, force = task
                elif len(task) == 4:
                    url, match_id, page_type, date_str = task
                elif len(task) == 3:
                    url, match_id, page_type = task
                else:
                    url, match_id = task
                    page_type = OkoooPageType.MOBILE_HISTORY # Default fallback
                
                # Default to today's date if not provided, to ensure archiving structure
                if not date_str:
                    date_str = datetime.now().strftime('%Y-%m-%d')
                
                # Check stop event after getting task
                if self._stop_event.is_set():
                    self.queue.task_done()
                    continue

                # 再次检查去重（防止队列中重复）
                if not force and await self.storage.is_duplicate(url):
                    await self._log("INFO", f"Skipping duplicate {url}")
                    self.stats["skipped"] += 1
                    self.stats["processed"] += 1
                    await self._update_progress()
                    self.queue.task_done()
                    continue

                await self._log("INFO", f"Processing {url}")
                
                # 下载
                html = await self.downloader.download(url)
                if not html:
                    await self._log("ERROR", f"Download failed for {url}")
                    self.stats["failed"] += 1
                    self.stats["processed"] += 1
                    await self._update_progress()
                    self.queue.task_done()
                    continue
                
                # 保存HTML文件
                try:
                    if filename is None:
                        filename = "unknown.html"
                        if page_type == OkoooPageType.MOBILE_HISTORY:
                            filename = "history.html"
                        elif page_type == OkoooPageType.MOBILE_ODDS:
                            filename = "odds.html"
                        elif page_type == OkoooPageType.MOBILE_HANDICAP:
                            filename = "handicap.html"
                        elif page_type == OkoooPageType.EXCHANGES:
                            filename = "exchanges.html"
                        elif page_type == OkoooPageType.AH:
                            filename = "handicap_ah.html"
                        elif page_type == OkoooPageType.MATCH_DETAIL:
                            filename = "game.html"
                    
                    await self.storage.save_html(match_id, filename, html, date_str=date_str)
                except Exception as e:
                    await self._log("ERROR", f"Failed to save HTML for {url}: {e}")

                # 解析 (目前只处理历史战绩页)
                if page_type == OkoooPageType.MOBILE_HISTORY or page_type == OkoooPageType.HISTORY:
                    try:
                        # Determine parser based on URL or config
                        if "m.okooo.com" in url:
                            parsed_data = self.parser.parse_mobile_history(html)
                        else:
                            parsed_data = self.parser.parse_history(html)
                            
                        # Detailed logging as requested
                        await self._log("INFO", f"正在解析页面：{url}")
                        if "match_info" in parsed_data:
                            m_info = parsed_data["match_info"]
                            await self._log("INFO", f"提取的数据字段：match_info")
                            await self._log("INFO", f"解析结果：{m_info}")
                            
                        # 补充ID信息
                        if "match_info" in parsed_data:
                            parsed_data["match_info"]["match_id"] = match_id
                            
                        # 存储解析数据
                        saved = await self.storage.save_match_data(parsed_data, source_url=url)
                        
                        # 额外保存为JSON文件 (Requested by user)
                        await self.storage.save_match_json(match_id, parsed_data)
                        
                        if saved:
                            await self._log("INFO", f"Saved match data to [DB/JSON] for match {match_id}")
                            self.stats["success"] += 1
                        else:
                            self.stats["failed"] += 1
                            
                    except Exception as e:
                        await self._log("ERROR", f"Parse failed for {url}: {e}")
                        self.stats["failed"] += 1
                        self.stats["processed"] += 1
                        await self._update_progress()
                        self.queue.task_done()
                        continue

                elif page_type == OkoooPageType.MOBILE_ODDS:
                    try:
                        parsed_data = self.parser.parse_mobile_odds(html)
                        
                        # Detailed logging
                        await self._log("INFO", f"正在解析页面：{url}")
                        if "euro_odds" in parsed_data:
                            odds_count = len(parsed_data["euro_odds"])
                            await self._log("INFO", f"提取的数据字段：euro_odds")
                            await self._log("INFO", f"解析结果：Found {odds_count} odds records")

                        # 存储解析数据 (Merge into JSON)
                        # DB storage for odds might need a specific method or update save_match_data to handle partial updates
                        # For now, we rely on save_match_json to merge into the file
                        await self.storage.save_match_json(match_id, parsed_data)
                        
                        # Also update DB if needed (optional for now as JSON is the primary request)
                        # await self.storage.save_match_data({"match_id": match_id, "odds_data": parsed_data}, source_url=url)
                        
                        await self._log("INFO", f"Saved odds data to JSON for match {match_id}")
                        self.stats["success"] += 1
                        
                    except Exception as e:
                        await self._log("ERROR", f"Parse odds failed for {url}: {e}")
                        self.stats["failed"] += 1

                else:
                    # 其他类型页面暂不解析入库，只保存文件
                    self.stats["success"] += 1
                    await self._log("INFO", f"Saved {filename} for match {match_id}")

                self.stats["processed"] += 1
                await self._update_progress()
                
                # 礼貌性延迟
                await asyncio.sleep(self.delay)
                self.queue.task_done()
                
            except asyncio.CancelledError:
                # Ensure task_done is called even if cancelled
                if 'task' in locals() and task is not None:
                    try:
                        self.queue.task_done()
                    except ValueError:
                        pass # Ignore if called too many times
                raise
                
            except Exception as e:
                await self._log("ERROR", f"Unexpected error: {e}")
                if 'task' in locals() and task is not None:
                    try:
                        self.queue.task_done()
                    except ValueError:
                        pass

        # await self._log("INFO", f"Worker {worker_id} stopped")

    async def crawl_lists(self, list_urls: List[str], force: bool = False):
        """
        爬取比赛列表并触发详情爬取
        """
        await self._init_components()
        all_match_ids = []
        
        for url in list_urls:
            try:
                list_type = "jczq" if "jczq" in url else "bjdc" if "bjdc" in url else "unknown"
                await self._log("INFO", f"Fetching list: {url} (Type: {list_type})")
                
                html = await self.downloader.download(url)
                if not html:
                    await self._log("ERROR", f"Failed to download list: {url}")
                    continue
                    
                # Parse matches
                if "m.okooo.com" in url:
                    matches = self.parser.parse_mobile_match_list(html)
                else:
                    matches = self.parser.parse_match_list(html)
                    
                # Filter new matches (optional check here or rely on crawl_ids)
                # But user wants "Found X new matches" log
                new_matches = []
                for m in matches:
                     # Check if we should process this match
                     # If force=False, we might want to check if it's already done?
                     # But crawl_ids does that too.
                     # Let's just count all found on page as "Found"
                     new_matches.append(m)
                     
                     # Also save basic info to DB if needed
                     await self.storage.save_basic_match_info(m)

                count = len(new_matches)
                await self._log("INFO", f"Found {count} new matches in {url}")
                
                all_match_ids.extend([m["match_id"] for m in new_matches])
                
            except Exception as e:
                await self._log("ERROR", f"Error processing list {url}: {e}")

        # Unique IDs
        unique_ids = list(set(all_match_ids))
        if unique_ids:
            # Include ODDS page in the crawl
            page_types = [OkoooPageType.MOBILE_HISTORY, OkoooPageType.MOBILE_ODDS]
            await self.crawl_ids(unique_ids, page_types=page_types, force=force)
        else:
            await self._log("INFO", "No matches found to crawl.")

    async def get_db_crawl_configs(self) -> List[Dict[str, Any]]:
        """
        Fetch crawl configurations from test_pages table where parent_id=4
        """
        configs = []
        try:
            async with self.db_manager.get_session() as session:
                from app.models.test_page import TestPage
                stmt = select(TestPage).where(TestPage.parent_id == 4, TestPage.is_active == True)
                result = await session.execute(stmt)
                pages = result.scalars().all()
                
                for page in pages:
                    url_lower = page.url.lower()
                    
                    p_type = OkoooPageType.MOBILE_HISTORY # Default
                    filename_prefix = "unknown"
                    
                    if "history.php" in url_lower:
                        p_type = OkoooPageType.MOBILE_HISTORY
                        filename_prefix = "history"
                    elif "odds.php" in url_lower:
                        p_type = OkoooPageType.MOBILE_ODDS
                        filename_prefix = "odds"
                    elif "handicap.php" in url_lower:
                        p_type = OkoooPageType.MOBILE_HANDICAP
                        filename_prefix = "handicap"
                    elif "exchanges.php" in url_lower:
                        p_type = OkoooPageType.MOBILE_EXCHANGES
                        filename_prefix = "exchanges"
                    elif "form.php" in url_lower:
                        p_type = OkoooPageType.MOBILE_FORM
                        filename_prefix = "form"
                    elif "game.php" in url_lower:
                        p_type = OkoooPageType.MOBILE_GAME
                        if "type=recent" in url_lower:
                             filename_prefix = "game_recent"
                        else:
                             filename_prefix = "game"
                    elif "change.php" in url_lower:
                        p_type = OkoooPageType.MOBILE_CHANGE
                        filename_prefix = "odds_change"
                    
                    configs.append({
                        "url_template": page.url,
                        "page_type": p_type,
                        "filename_prefix": filename_prefix,
                        "id": page.id
                    })
        except Exception as e:
            logger.error(f"Failed to load crawl configs: {e}")
            
        return configs

    async def crawl_ids(self, match_ids: List[str], page_types: Optional[List[OkoooPageType]] = None, date_str: Optional[str] = None, force: bool = False):
        """
        爬取指定ID列表的比赛
        """
        # Load configs from DB
        configs = await self.get_db_crawl_configs()
        
        self._stop_event.clear()
        
        # Calculate total tasks based on configs or fallback
        tasks_per_match = len(configs) if configs else (len(page_types) if page_types else 1)
        
        self.stats = {
            "total": len(match_ids) * tasks_per_match,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        await self._init_components()
        await self._log("INFO", f"Starting crawl for {len(match_ids)} matches with {tasks_per_match} pages each (Force: {force})")
        
        # 启动Workers
        workers = []
        for i in range(self.concurrency):
            workers.append(asyncio.create_task(self._worker(i)))
            
        count = 0
        skipped = 0
        
        try:
            for str_id in match_ids:
                if self._stop_event.is_set():
                    break
                
                if configs:
                    # Use DB configs
                    for config in configs:
                        url_template = config["url_template"]
                        # Replace MatchID=... or mid=...
                        # Use regex to replace the existing ID value with the new one
                        url = re.sub(r'MatchID=\d+', f'MatchID={str_id}', url_template)
                        url = re.sub(r'mid=\d+', f'mid={str_id}', url)
                        
                        # Determine filename
                        filename_prefix = config["filename_prefix"]
                        filename = f"{filename_prefix}_{str_id}.html"
                        
                        # Handle change.php specifically for pid
                        if "change.php" in url:
                            pid_match = re.search(r'pid=(\d+)', url)
                            if pid_match:
                                pid = pid_match.group(1)
                                filename = f"{filename_prefix}_{str_id}_{pid}.html"
                        
                        # Check duplicate
                        if not force and await self.storage.is_duplicate(url):
                            await self._log("INFO", f"Skipping duplicate {url}")
                            skipped += 1
                            self.stats["skipped"] += 1
                            self.stats["processed"] += 1
                            continue
                        
                        # Queue task with explicit filename
                        # Tuple: (url, match_id, page_type, date_str, force, filename)
                        self.queue.put_nowait((url, str_id, config["page_type"], date_str, force, filename))
                        count += 1
                else:
                    # Fallback to legacy behavior
                    if page_types is None:
                        page_types = [OkoooPageType.MOBILE_HISTORY]
                    
                    for p_type in page_types:
                        url = self.url_builder.build_match_url(str_id, p_type)
                        
                        if not force and await self.storage.is_duplicate(url):
                            await self._log("INFO", f"Skipping duplicate {url}")
                            skipped += 1
                            self.stats["skipped"] += 1
                            self.stats["processed"] += 1
                            continue
                        
                        self.queue.put_nowait((url, str_id, p_type, date_str, force))
                        count += 1
                
            await self._log("INFO", f"Queued {count} tasks. Skipped {skipped} duplicates.")
            
            # 等待所有任务完成
            await self.queue.join()
            
        except Exception as e:
            await self._log("ERROR", f"Crawl ids exception: {e}")
        finally:
            self._stop_event.set()
            # Cancel all workers immediately to ensure stop
            for w in workers:
                if not w.done():
                    w.cancel()
            
            # Wait for workers to handle cancellation
            await asyncio.gather(*workers, return_exceptions=True)
            
            await self._log("INFO", "Crawl ids finished")

    async def get_config_page_types(self) -> List[OkoooPageType]:
        """
        从test_pages表中获取parent_id=4的配置，并映射为OkoooPageType
        """
        page_types = []
        try:
            async with self.db_manager.get_session() as session:
                from app.models.test_page import TestPage
                
                stmt = select(TestPage).where(TestPage.parent_id == 4, TestPage.is_active == True)
                result = await session.execute(stmt)
                pages = result.scalars().all()
                
                for page in pages:
                    # Map based on name or url keywords
                    # Check platform or url for mobile/pc distinction if needed, currently defaulting to mobile types if ambiguous for mobile crawler
                    name_lower = page.name.lower()
                    url_lower = page.url.lower()
                    
                    if "history" in name_lower or "战绩" in name_lower:
                        page_types.append(OkoooPageType.MOBILE_HISTORY)
                    elif "odds" in name_lower or "欧指" in name_lower or "欧赔" in name_lower:
                        page_types.append(OkoooPageType.MOBILE_ODDS)
                    elif "handicap" in name_lower or "亚指" in name_lower or "亚盘" in name_lower:
                        page_types.append(OkoooPageType.MOBILE_HANDICAP)
                    elif "exchange" in name_lower or "盈亏" in name_lower or "必发" in name_lower:
                        page_types.append(OkoooPageType.EXCHANGES)
                    elif "ah" in name_lower:
                        page_types.append(OkoooPageType.AH)
                    elif "detail" in name_lower or "详情" in name_lower or "积分" in name_lower or "game" in name_lower:
                        page_types.append(OkoooPageType.MATCH_DETAIL)
                    elif "form" in name_lower or "阵容" in name_lower:
                        # Assuming form is part of history or separate, but mapping to history for now if no specific type
                        # Or maybe we need a new type? Let's check UrlBuilder if possible.
                        # For now, just map to MOBILE_HISTORY as it often contains form
                        page_types.append(OkoooPageType.MOBILE_HISTORY)
                        
        except Exception as e:
            await self._log("ERROR", f"Failed to load config from test_pages: {e}")
            
        return list(set(page_types))  # Unique

    async def fetch_match_lists(self) -> List[Dict[str, Any]]:
        """
        获取比赛列表（不爬取详情）
        """
        await self._init_components()
        
        urls = [
            "https://m.okooo.com/jczq/",
            "https://m.okooo.com/bjdc/"
        ]
        
        all_matches = []
        seen_ids = set()
        
        try:
            for url in urls:
                match_type = "jczq"
                if "bjdc" in url:
                    match_type = "bjdc"
                    
                await self._log("INFO", f"Fetching list: {url} (Type: {match_type})")
                html = await self.downloader.download(url)
                if html:
                    # Use mobile parser since we are using mobile UA
                    matches = self.parser.parse_mobile_match_list(html)
                    new_count = 0
                    for m in matches:
                        mid = m['match_id']
                        if mid and mid not in seen_ids:
                            seen_ids.add(mid)
                            m['match_type'] = match_type
                            all_matches.append(m)
                            new_count += 1
                            # Save to DB immediately
                            await self.storage.save_basic_match_info(m)
                            
                    await self._log("INFO", f"Found {new_count} new matches in {url}")
                else:
                    await self._log("ERROR", f"Failed to download list: {url}")
            
            # Broadcast found matches
            if self.match_list_callback and all_matches:
                try:
                    await self.match_list_callback(all_matches)
                except Exception as e:
                    logger.error(f"Match list callback failed: {e}")
                    
        except Exception as e:
            await self._log("ERROR", f"Error fetching lists: {e}")
            
        return all_matches

    async def crawl_match_lists(self, page_types: Optional[List[OkoooPageType]] = None):
        """
        从比赛列表页面爬取
        """
        if page_types is None:
            # Try to load from DB config first
            page_types = await self.get_config_page_types()
            
            # If no config found, fallback to defaults
            if not page_types:
                await self._log("WARNING", "No crawl config found in test_pages (parent_id=4), using defaults")
                page_types = [
                    OkoooPageType.MOBILE_HISTORY,
                    OkoooPageType.MOBILE_ODDS,
                    OkoooPageType.MOBILE_HANDICAP
                ]
            else:
                await self._log("INFO", f"Loaded crawl config from DB: {[pt.value for pt in page_types]}")

        # Fetch first
        matches = await self.fetch_match_lists()
        
        # Use current date for archiving folder
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if matches:
            match_ids = []
            for m in matches:
                # Basic info already saved in fetch_match_lists
                if m.get('match_id'):
                    match_ids.append(m['match_id'])
            
            await self._log("INFO", f"Total unique matches to crawl: {len(match_ids)}")
            if match_ids:
                await self.crawl_ids(match_ids, page_types, date_str=current_date)
        else:
            await self._log("WARNING", "No matches found to crawl")

    async def crawl_range(self, start_id: int, end_id: int, page_type: OkoooPageType = OkoooPageType.MOBILE_HISTORY):
        """
        爬取指定ID范围的比赛
        """
        self._stop_event.clear()
        self.stats = {
            "total": end_id - start_id + 1,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        await self._init_components()
        await self._log("INFO", f"Starting crawl range: {start_id} to {end_id}")
        
        # 生产任务
        count = 0
        skipped = 0
        
        # 启动Workers
        workers = []
        for i in range(self.concurrency):
            workers.append(asyncio.create_task(self._worker(i)))
        
        try:
            for match_id in range(start_id, end_id + 1):
                if self._stop_event.is_set():
                    break
                    
                str_id = str(match_id)
                url = self.url_builder.build_match_url(str_id, page_type)
                
                # 预检查去重（断点续传核心）
                if await self.storage.is_duplicate(url):
                    skipped += 1
                    self.stats["skipped"] += 1
                    self.stats["processed"] += 1
                    if skipped % 100 == 0:
                        await self._log("INFO", f"Skipped {skipped} duplicates so far...")
                    continue
                    
                await self.queue.put((url, str_id, page_type))
                count += 1
                
            await self._log("INFO", f"Queued {count} tasks. Skipped {skipped} already processed tasks.")
            await self._update_progress()
            
            # 等待所有任务完成
            await self.queue.join()
            
        except Exception as e:
             await self._log("ERROR", f"Crawl range exception: {e}")
        finally:
            self._stop_event.set()
            # 发送停止信号
            for _ in range(self.concurrency):
                await self.queue.put(None)
            
            await asyncio.gather(*workers)
            await self._log("INFO", "Crawl range finished")

    def stop(self):
        """停止爬取"""
        self._stop_event.set()

    async def close(self):
        """清理资源"""
        self.stop()
        if self.downloader:
            await self.downloader.close()
