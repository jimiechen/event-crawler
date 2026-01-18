import httpx
from loguru import logger

class BackendClient:
    BASE_URL = "http://localhost:8002/api/v1"

    @classmethod
    async def trigger_calculation(cls, date_str: str, batch_id: int = 0):
        """
        调用后端API触发评分计算
        GET /api/v1/scores/calculate/{date}/{batch_id}
        """
        url = f"{cls.BASE_URL}/scores/calculate/{date_str}/{batch_id}"
        logger.info(f"Triggering calculation via {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to trigger calculation: {e}")
                raise e

    @classmethod
    async def trigger_single_calculation(cls, date_str: str, code: str):
        """
        调用后端API触发单只股票评分计算
        GET /api/v1/scores/calculate/{date}/{code}
        """
        url = f"{cls.BASE_URL}/scores/calculate/{date_str}/{code}"
        logger.info(f"Triggering single calculation via {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to trigger single calculation: {e}")
                raise e

    @classmethod
    async def trigger_volume_analysis(cls, code: str):
        """
        调用后端API触发单只股票成交量异动分析
        GET /api/v1/volume-analysis/run/{code}
        """
        url = f"{cls.BASE_URL}/volume-analysis/run/{code}"
        logger.info(f"Triggering volume analysis via {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to trigger volume analysis: {e}")
                raise e

    @classmethod
    async def call_wencai_crawler(cls, crawl_date: str):
        """
        调用后端API执行问财爬虫
        GET /api/v1/wencai/crawler/{crawl_date}/1
        """
        url = f"{cls.BASE_URL}/wencai/crawler/{crawl_date}/1"
        logger.info(f"Calling Wencai Crawler via {url}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to call Wencai Crawler: {e}")
                raise e
