import sys
import os
import asyncio
from typing import List, Dict, Type
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# Add module-playwright-crawler to sys.path
MODULE_PATH = "/Users/mac/StudioProjects/open-citycloud/modules/module-playwright-crawler/src"
if MODULE_PATH not in sys.path:
    sys.path.append(MODULE_PATH)

try:
    from playwright_crawler.crawler_base import CrawlerBase
    from playwright_crawler.weibo_crawler import WeiboCrawler
    from playwright_crawler.douyin_crawler import DouyinCrawler
    from playwright_crawler.xiaohongshu_crawler import XiaohongshuCrawler
    from playwright_crawler.bilibili_crawler import BilibiliCrawler
    from playwright_crawler.okooo_crawler import OkoooCrawler
except ImportError as e:
    logger.error(f"Failed to import crawler modules: {e}")
    # Define dummy classes to avoid crashing if module is missing during development
    class CrawlerBase: pass
    class WeiboCrawler: pass
    class DouyinCrawler: pass
    class XiaohongshuCrawler: pass
    class BilibiliCrawler: pass
    class OkoooCrawler: pass

from app.repositories.crawler_repository import CrawlerTargetRepository, CrawlerResultRepository
from app.models.crawler import CrawlerResult, CrawlerTarget

class CrawlerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.target_repo = CrawlerTargetRepository(session)
        self.result_repo = CrawlerResultRepository(session)
        
        self.crawler_map: Dict[str, Type[CrawlerBase]] = {
            "weibo": WeiboCrawler,
            "douyin": DouyinCrawler,
            "xiaohongshu": XiaohongshuCrawler,
            "bilibili": BilibiliCrawler,
            "okooo": OkoooCrawler
        }

    async def execute_all_crawlers(self):
        """
        Execute crawlers for all active targets.
        """
        logger.info("Starting batch crawler execution...")
        
        # 1. Fetch active targets
        targets = await self.target_repo.find_active_targets()
        if not targets:
            logger.info("No active crawler targets found.")
            return

        logger.info(f"Found {len(targets)} active targets.")

        # 2. Group by platform
        targets_by_platform: Dict[str, List[CrawlerTarget]] = {}
        for target in targets:
            if target.platform not in targets_by_platform:
                targets_by_platform[target.platform] = []
            targets_by_platform[target.platform].append(target)

        # 3. Execute per platform
        for platform, platform_targets in targets_by_platform.items():
            crawler_cls = self.crawler_map.get(platform)
            if not crawler_cls:
                logger.warning(f"No crawler implementation found for platform: {platform}")
                continue

            logger.info(f"Executing {platform} crawler for {len(platform_targets)} targets...")
            
            try:
                # Instantiate crawler
                # Note: Config is loaded from default path in CrawlerBase. 
                # We might need to ensure the config file exists or is accessible.
                # Assuming the backend runs in a place where it can find the config or we might need to patch it.
                # For now, let's try instantiation.
                crawler = crawler_cls()
                
                # Override backend_url if needed (assuming localhost:8000 for self-reporting)
                crawler.backend_url = "http://localhost:8000"
                
                # Update config to ensure we don't crawl too much per target in this batch mode
                # crawler.platform_config['max_count'] = 10 # Example limit
                
                for target in platform_targets:
                    logger.info(f"Crawling target: {target.name} ({target.url})")
                    
                    try:
                        # Determine keyword/url
                        # If target_type is 'url', we might need to extract keyword or use url directly
                        # The crawlers (e.g. Weibo) seem to take a 'keyword' and form a search URL.
                        # If the user provided a full URL, we might need to handle it.
                        # For now, let's assume 'url' field contains the keyword if target_type is 'keyword', 
                        # or the full URL if target_type is 'url'.
                        # The existing crawlers seem to expect a 'keyword'.
                        
                        search_term = target.url
                        if target.target_type == 'url' and platform == 'weibo':
                            # Weibo crawler expects keyword for search. 
                            # If it's a direct URL, the current implementation might not support it directly
                            # unless we modify the crawler.
                            # But for now, let's pass it as is.
                            pass
                            
                        # Run crawl
                        # We use a timeout to prevent one target blocking everything
                        data_list = await asyncio.wait_for(
                            crawler.crawl(keyword=search_term, max_count=5), 
                            timeout=120
                        )
                        
                        # Save results
                        count = 0
                        for item in data_list:
                            # Map CrawlerData (dict) to CrawlerResult model
                            # CrawlerData keys: content, author, time, likes, comments, shares, url, id
                            
                            # Parse time
                            publish_time = None
                            if item.get('time'):
                                try:
                                    # Attempt parsing, might need robust parsing logic
                                    # For now, ignore if parse fails or use current time
                                    pass 
                                except:
                                    pass

                            result = CrawlerResult(
                                platform=platform,
                                target_id=target.id,
                                content=item.get('content'),
                                author=item.get('author'),
                                likes=item.get('likes', 0),
                                comments=item.get('comments', 0),
                                shares=item.get('shares', 0),
                                url=item.get('url'),
                                data_id=item.get('id'),
                                crawled_at=datetime.now()
                            )
                            await self.result_repo.create(result)
                            count += 1
                        
                        # Update target status
                        target.last_crawled_at = datetime.now()
                        target.last_status = "success"
                        await self.session.commit() # Commit updates
                        
                        logger.info(f"Target {target.name} crawled successfully. Saved {count} results.")
                        
                    except Exception as e:
                        logger.error(f"Failed to crawl target {target.name}: {e}")
                        target.last_status = "failed"
                        # We don't commit here to avoid breaking the loop? No, we should commit the status update.
                        try:
                            await self.session.commit()
                        except:
                            await self.session.rollback()

            except Exception as e:
                logger.error(f"Error initializing or running {platform} crawler: {e}")

        logger.info("Batch crawler execution completed.")

    async def check_login_status(self, platform: str, url: str = None, nickname_xpath: str = None) -> Dict[str, Any]:
        """
        Check login status for a platform.
        """
        crawler_cls = self.crawler_map.get(platform)
        if not crawler_cls:
            return {"logged_in": False, "message": f"Platform {platform} not supported"}
        
        try:
            # Instantiate crawler (loads config automatically)
            crawler = crawler_cls()
            
            if not url:
                default_urls = {
                    "weibo": "https://weibo.com",
                    "douyin": "https://www.douyin.com",
                    "xiaohongshu": "https://www.xiaohongshu.com",
                    "bilibili": "https://www.bilibili.com",
                    "okooo": "https://www.okooo.com"
                }
                url = default_urls.get(platform)
            
            if not url:
                return {"logged_in": False, "message": "URL is required"}

            # Call the check_login_status method we added to CrawlerBase
            # Note: The import path hack might make IDE complain but runtime should be fine
            # provided the module code is updated.
            return await crawler.check_login_status(url, nickname_xpath)
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return {"logged_in": False, "message": str(e)}
