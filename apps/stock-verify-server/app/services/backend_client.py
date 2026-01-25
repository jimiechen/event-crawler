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
        
        async with httpx.AsyncClient(timeout=120.0) as client:
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

    @classmethod
    async def get_wencai_stocks(cls, batch_id: int):
        """
        调用后端API获取问财股票数据
        GET /api/v1/wencai/stocks?batch_id={batch_id}
        """
        url = f"{cls.BASE_URL}/wencai/stocks?batch_id={batch_id}&limit=1000"
        logger.info(f"Fetching Wencai stocks via {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to fetch Wencai stocks: {e}")
                raise e

    @classmethod
    async def load_local_data(cls, codes: list, end_date: str = None):
        """
        调用后端API加载本地数据
        POST /api/v1/test-tool/load-local-data
        """
        url = f"{cls.BASE_URL}/test-tool/load-local-data"
        logger.info(f"Loading local data via {url}")
        
        payload = {"codes": codes}
        if end_date:
            payload["end_date"] = end_date
            
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to load local data: {e}")
                raise e

    @classmethod
    async def stream_simulation(cls, date_str: str):
        """
        调用后端API流式获取仿真日志
        GET /api/v1/simulation/run/{date}
        """
        url = f"{cls.BASE_URL}/simulation/run/{date_str}"
        logger.info(f"Streaming simulation from {url}")
        
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    yield line + "\n"

    @classmethod
    async def validate_data_counts(cls, codes: list, min_count: int = 250):
        """
        调用后端API验证数据数量
        POST /api/v1/test-tool/validate-data-counts
        """
        url = f"{cls.BASE_URL}/test-tool/validate-data-counts"
        logger.info(f"Validating data counts via {url}")
        
        payload = {"codes": codes, "min_count": min_count}
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to validate data counts: {e}")
                raise e

