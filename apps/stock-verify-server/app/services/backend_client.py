import httpx
from loguru import logger

class BackendClient:
    BASE_URL = "http://localhost:8000/api/v1"

    async def search_wencai(self, query: str):
        async with httpx.AsyncClient() as client:
            try:
                # Assuming endpoint structure based on controller names
                # wencai_controller.py likely has a search endpoint
                resp = await client.post(f"{self.BASE_URL}/wencai/search", json={"query": query})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to call wencai search: {e}")
                return None

    async def sync_history(self, code: str):
        async with httpx.AsyncClient() as client:
            try:
                # stock_sync_controller.py
                resp = await client.post(f"{self.BASE_URL}/stock/sync/history", params={"code": code})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to call history sync: {e}")
                return None

    async def run_volume_analysis(self, code: str):
        async with httpx.AsyncClient() as client:
            try:
                # volume_analysis_controller.py
                resp = await client.post(f"{self.BASE_URL}/analysis/volume", params={"code": code})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to call volume analysis: {e}")
                return None
