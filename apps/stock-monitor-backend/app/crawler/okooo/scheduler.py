# -*- coding: utf-8 -*-
import asyncio
import logging
from typing import List, Optional
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

    async def _init_components(self):
        """初始化组件"""
        if not self.downloader:
            self.downloader = OkoooDownloader(headless=True)
        if not self.storage:
            self.storage = OkoooStorage(self.db_manager, self.redis_service)

    async def _worker(self, worker_id: int):
        """工作协程"""
        logger.info(f"Worker {worker_id} started")
        while True:
            try:
                # 获取任务
                task = await self.queue.get()
                if task is None: # 结束信号
                    self.queue.task_done()
                    break
                
                url, match_id = task
                
                # 再次检查去重（防止队列中重复）
                if await self.storage.is_duplicate(url):
                    logger.info(f"Worker {worker_id}: Skipping duplicate {url}")
                    self.queue.task_done()
                    continue

                logger.info(f"Worker {worker_id}: Processing {url}")
                
                # 下载
                html = await self.downloader.download(url)
                if not html:
                    logger.error(f"Worker {worker_id}: Download failed for {url}")
                    # TODO: 可以在这里实现重试逻辑
                    self.queue.task_done()
                    continue
                
                # 解析
                try:
                    # 目前主要针对History页面
                    parsed_data = self.parser.parse_history(html)
                    # 补充ID信息
                    if "match_info" in parsed_data:
                        parsed_data["match_info"]["match_id"] = match_id
                except Exception as e:
                    logger.error(f"Worker {worker_id}: Parse failed for {url}: {e}")
                    self.queue.task_done()
                    continue

                # 存储
                saved = await self.storage.save_match_data(parsed_data, source_url=url)
                if saved:
                    logger.info(f"Worker {worker_id}: Saved data for match {match_id}")
                
                # 礼貌性延迟
                await asyncio.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"Worker {worker_id}: Unexpected error: {e}")
            finally:
                if 'task' in locals() and task is not None:
                    self.queue.task_done()

        logger.info(f"Worker {worker_id} stopped")

    async def crawl_range(self, start_id: int, end_id: int, page_type: OkoooPageType = OkoooPageType.HISTORY):
        """
        爬取指定ID范围的比赛
        """
        await self._init_components()
        
        # 启动Workers
        workers = []
        for i in range(self.concurrency):
            workers.append(asyncio.create_task(self._worker(i)))
            
        logger.info(f"Starting crawl range: {start_id} to {end_id}")
        
        # 生产任务
        count = 0
        skipped = 0
        
        for match_id in range(start_id, end_id + 1):
            str_id = str(match_id)
            url = self.url_builder.build_match_url(str_id, page_type)
            
            # 预检查去重（断点续传核心）
            if await self.storage.is_duplicate(url):
                skipped += 1
                if skipped % 100 == 0:
                    logger.info(f"Skipped {skipped} duplicates so far...")
                continue
                
            await self.queue.put((url, str_id))
            count += 1
            
        logger.info(f"Queued {count} tasks. Skipped {skipped} already processed tasks.")
        
        # 等待所有任务完成
        await self.queue.join()
        
        # 发送停止信号
        for _ in range(self.concurrency):
            await self.queue.put(None)
        
        await asyncio.gather(*workers)
        logger.info("Crawl range finished")

    async def close(self):
        """清理资源"""
        if self.downloader:
            await self.downloader.close()
