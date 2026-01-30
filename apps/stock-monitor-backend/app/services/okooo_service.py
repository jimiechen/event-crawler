# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
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
        return cls._instance

    def __init__(self):
        # 已经在__new__中初始化，避免重复初始化
        pass

    async def get_db_matches(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从数据库获取比赛列表
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(OkoooMatch)
                
                if date_str:
                    stmt = stmt.where(OkoooMatch.match_date == date_str)
                
                # Order by match time or ID
                stmt = stmt.order_by(desc(OkoooMatch.match_date), desc(OkoooMatch.id))
                
                result = await session.execute(stmt)
                matches = result.scalars().all()
                
                return [{
                    "id": m.id,
                    "match_id": m.match_id,
                    "league": m.league_name,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "match_time": m.match_time_text,
                    "match_date": m.match_date,
                    "history_data": m.history_data
                } for m in matches]
        except Exception as e:
            logger.error(f"Error getting db matches: {e}")
            return []

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
        await manager.broadcast(log_data)
        await sse_service.broadcast("okooo_log", log_data)

    async def _on_progress(self, processed: int, total: int):
        """进度回调"""
        progress_data = {
            "type": "okooo_progress",
            "processed": processed,
            "total": total,
            "percentage": round(processed / total * 100, 2) if total > 0 else 0
        }
        await manager.broadcast(progress_data)
        await sse_service.broadcast("okooo_progress", progress_data)

    async def _on_match_list(self, matches: list):
        """比赛列表回调"""
        data = {
            "type": "okooo_matches",
            "matches": matches
        }
        await manager.broadcast(data)
        await sse_service.broadcast("okooo_matches", data)

    async def repair_daily_data(self, date_str: str) -> Dict[str, Any]:
        """
        检查指定日期的比赛数据完整性，并重新爬取缺失或无效的比赛
        """
        import os
        
        # 1. Get matches from DB
        matches = await self.get_db_matches(date_str)
        if not matches:
             return {"total": 0, "repaired": 0, "message": "No matches found for date", "ids": []}
             
        # 2. Check files
        base_dir = os.path.join(os.getcwd(), "data", "okooo", "matches", date_str)
        ids_to_crawl = []
        
        # Expected file count is 8, but we'll accept 7 as well to be lenient, or strict 8?
        # User said "only 6/8", so 8 is likely the target.
        # Let's check for specific critical files.
        # Prefixes based on user info.
        
        for m in matches:
            mid = m.get('match_id')
            if not mid: continue
            
            match_dir = os.path.join(base_dir, mid)
            
            # If directory doesn't exist, definitely re-crawl
            if not os.path.exists(match_dir):
                ids_to_crawl.append(mid)
                continue
                
            # Check file count
            files = os.listdir(match_dir)
            html_files = [f for f in files if f.endswith('.html')]
            
            # User mentioned 6/8. So if < 8, we might want to repair.
            # Strictly check for 8 files as per user requirement
            if len(html_files) < 8:
                 ids_to_crawl.append(mid)
                 continue
                 
            # Check for invalid files (small size)
            has_invalid = False
            for f in html_files:
                fpath = os.path.join(match_dir, f)
                # Check size < 2KB (empty or error page)
                if os.path.getsize(fpath) < 2048: 
                    has_invalid = True
                    break
            
            if has_invalid:
                ids_to_crawl.append(mid)
                continue

        # 3. Start crawling if needed
        if ids_to_crawl:
            # Trigger crawl in background
            await self.start_crawl_ids(ids_to_crawl, headless=True, force=True)
            
        return {
            "total_checked": len(matches), 
            "repairing_count": len(ids_to_crawl), 
            "ids": ids_to_crawl,
            "message": f"Found {len(ids_to_crawl)} matches to repair out of {len(matches)}"
        }

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

    async def start_crawl_ids(self, match_ids: list, headless: bool = True, use_cache: bool = False, force: bool = False, use_proxy: bool = False) -> bool:
        """启动指定ID列表爬虫任务"""
        if self.is_running:
            logger.warning("Okooo crawler is already running")
            return False

        scheduler = await self.get_scheduler()
        
        # Configure
        storage_path = "okooo_session.json" if use_cache else None
        await scheduler.configure(headless=headless, storage_state_path=storage_path, use_proxy=use_proxy)
        
        self.is_running = True
        
        # 创建后台任务
        self._crawl_task = asyncio.create_task(self._run_crawl_ids(scheduler, match_ids, force))
        return True

    async def _run_crawl_ids(self, scheduler: OkoooScheduler, match_ids: list, force: bool = False):
        """执行ID列表爬虫任务的包装器"""
        try:
            await scheduler.crawl_ids(match_ids, force=force)
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

    def _get_filename_by_type(self, page_type: Optional[str], match_id: str) -> str:
        """根据页面类型生成文件名"""
        filename_map = {
            "澳客欧赔": "odds",
            "澳客亚盘": "handicap",
            "澳客历史": "history",
            "澳客阵容": "form",
            "澳客盈亏": "exchanges",
            "澳客积分": "table",
            "澳客澳门亚盘变化": "odds_change"
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
        page_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存比赛详情页面 HTML
        保存到 data/okooo/matches/[date]/[match_id]/
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
            filename = self._get_filename_by_type(page_type, match_id)
            save_path = os.path.join(save_dir, filename)

            # 保存 HTML 文件
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(html)

            logger.info(f"[OkoooMatch] 保存成功: {save_path}")

            # 发送 SSE 通知
            await sse_service.broadcast("okooo_file_saved", {
                "match_id": match_id,
                "page_type": page_type or "index",
                "filename": filename,
                "path": save_path
            })

            return {
                "success": True,
                "match_id": match_id,
                "url": url,
                "save_path": save_path,
                "html_size": len(html),
                "captured_at": captured_at,
                "date": date,
                "page_type": page_type
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
        date: str
    ) -> Dict[str, Any]:
        """
        保存让球盘页面 HTML（由浏览器扩展直接获取 HTML）
        保存到 data/okooo/matches/[date]/[match_id]/handicap.html
        """
        import os
        import re
        import aiofiles

        try:
            # 验证内容
            self._validate_html_content(html)

            # 构建保存路径 (统一到 matches 目录)
            save_dir = os.path.abspath(os.path.join(
                os.getcwd(), "data", "okooo", "matches", date, match_id
            ))
            os.makedirs(save_dir, exist_ok=True)

            # 保存 HTML 文件
            save_path = os.path.join(save_dir, "handicap.html")
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(html)

            logger.info(f"[OkoooHandicap] 保存成功: {save_path}")

            # 发送 SSE 通知
            await sse_service.broadcast("okooo_file_saved", {
                "match_id": match_id,
                "page_type": "handicap",
                "filename": "handicap.html",
                "path": save_path
            })

            return {
                "success": True,
                "match_id": match_id,
                "url": url,
                "save_path": save_path,
                "html_size": len(html),
                "captured_at": captured_at,
                "date": date
            }

        except Exception as e:
            logger.error(f"[OkoooHandicap] 保存失败 {match_id}: {e}")
            raise

# 全局实例
okooo_service = OkoooService()
