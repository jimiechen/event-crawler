# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Callable, Awaitable, Dict, Any
from asyncio import Queue

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
                 concurrency: int = 5,
                 delay: float = 1.0):
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

    async def configure(self, headless: bool = True, is_mobile: bool = True, storage_state_path: Optional[str] = None):
        """配置爬虫参数"""
        # 如果配置有变化，且downloader已存在，则关闭旧的以便重新初始化
        config_changed = (
            self.headless != headless or 
            self.is_mobile != is_mobile or 
            self.storage_state_path != storage_state_path
        )
        
        self.headless = headless
        self.is_mobile = is_mobile
        self.storage_state_path = storage_state_path
        
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
            self.downloader = OkoooDownloader(
                headless=self.headless,
                is_mobile=self.is_mobile,
                storage_state_path=self.storage_state_path
            )
        if not self.storage:
            self.storage = OkoooStorage(self.db_manager, self.redis_service)

    async def _worker(self, worker_id: int):
        """工作协程"""
        await self._log("INFO", f"Worker {worker_id} started")
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
                
                # Support 4-tuple (url, match_id, page_type, date_str), 3-tuple or 2-tuple
                date_str = None
                if len(task) == 4:
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
                if await self.storage.is_duplicate(url):
                    await self._log("INFO", f"Worker {worker_id}: Skipping duplicate {url}")
                    self.stats["skipped"] += 1
                    self.stats["processed"] += 1
                    await self._update_progress()
                    self.queue.task_done()
                    continue

                await self._log("INFO", f"Worker {worker_id}: Processing {url}")
                
                # 下载
                html = await self.downloader.download(url)
                if not html:
                    await self._log("ERROR", f"Worker {worker_id}: Download failed for {url}")
                    self.stats["failed"] += 1
                    self.stats["processed"] += 1
                    await self._update_progress()
                    self.queue.task_done()
                    continue
                
                # 保存HTML文件
                try:
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
                    await self._log("ERROR", f"Worker {worker_id}: Failed to save HTML for {url}: {e}")

                # 解析 (目前只处理历史战绩页)
                if page_type == OkoooPageType.MOBILE_HISTORY or page_type == OkoooPageType.HISTORY:
                    try:
                        # Determine parser based on URL or config
                        if "m.okooo.com" in url:
                            parsed_data = self.parser.parse_mobile_history(html)
                        else:
                            parsed_data = self.parser.parse_history(html)
                            
                        # 补充ID信息
                        if "match_info" in parsed_data:
                            parsed_data["match_info"]["match_id"] = match_id
                            
                        # 存储解析数据
                        saved = await self.storage.save_match_data(parsed_data, source_url=url)
                        if saved:
                            await self._log("INFO", f"Worker {worker_id}: Saved data for match {match_id}")
                            self.stats["success"] += 1
                        else:
                            self.stats["failed"] += 1
                            
                    except Exception as e:
                        await self._log("ERROR", f"Worker {worker_id}: Parse failed for {url}: {e}")
                        self.stats["failed"] += 1
                        self.stats["processed"] += 1
                        await self._update_progress()
                        self.queue.task_done()
                        continue
                else:
                    # 其他类型页面暂不解析入库，只保存文件
                    self.stats["success"] += 1
                    await self._log("INFO", f"Worker {worker_id}: Saved {filename} for match {match_id}")

                self.stats["processed"] += 1
                await self._update_progress()
                
                # 礼貌性延迟
                await asyncio.sleep(self.delay)
                self.queue.task_done()
                
            except Exception as e:
                await self._log("ERROR", f"Worker {worker_id}: Unexpected error: {e}")
                if 'task' in locals() and task is not None:
                    self.queue.task_done()

        await self._log("INFO", f"Worker {worker_id} stopped")

    async def crawl_ids(self, match_ids: List[str], page_types: Optional[List[OkoooPageType]] = None, date_str: Optional[str] = None):
        """
        爬取指定ID列表的比赛
        """
        if page_types is None:
            page_types = [OkoooPageType.MOBILE_HISTORY]
            
        self._stop_event.clear()
        self.stats = {
            "total": len(match_ids) * len(page_types),
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        await self._init_components()
        await self._log("INFO", f"Starting crawl for {len(match_ids)} matches with {len(page_types)} pages each")
        
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
                
                for p_type in page_types:
                    url = self.url_builder.build_match_url(str_id, p_type)
                    
                    # 预检查去重
                    if await self.storage.is_duplicate(url):
                        skipped += 1
                        self.stats["skipped"] += 1
                        self.stats["processed"] += 1
                        continue
                        
                    await self.queue.put((url, str_id, p_type, date_str))
                    count += 1
                
            await self._log("INFO", f"Queued {count} tasks. Skipped {skipped} duplicates.")
            await self._update_progress()
            
            await self.queue.join()
            
        except Exception as e:
            await self._log("ERROR", f"Crawl ids exception: {e}")
        finally:
            self._stop_event.set()
            for _ in range(self.concurrency):
                await self.queue.put(None)
            await asyncio.gather(*workers)
            await self._log("INFO", "Crawl ids finished")

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
                await self._log("INFO", f"Fetching list: {url}")
                html = await self.downloader.download(url)
                if html:
                    # Use mobile parser since we are using mobile UA
                    matches = self.parser.parse_mobile_match_list(html)
                    new_count = 0
                    for m in matches:
                        mid = m['match_id']
                        if mid and mid not in seen_ids:
                            seen_ids.add(mid)
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
            # Default to fetching history, odds, and handicap for mobile
            page_types = [
                OkoooPageType.MOBILE_HISTORY,
                OkoooPageType.MOBILE_ODDS,
                OkoooPageType.MOBILE_HANDICAP
            ]

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
