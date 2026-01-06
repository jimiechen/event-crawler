from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

class Verifier:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def verify_data_exists(self, stock_code: str, table: str, condition: str = None):
        try:
            col_name = "code" if table in ["stock_daily", "stock_info"] else "stock_code"
            # specific override
            if table == "monitor_list": col_name = "stock_code"
            
            query = f"SELECT count(*) FROM {table} WHERE {col_name} = :code"
            if condition:
                query += f" AND {condition}"
                
            result = await self.session.execute(text(query), {"code": stock_code})
            count = result.scalar()
            return {"table": table, "exists": count > 0, "count": count}
        except Exception as e:
            return {"table": table, "error": str(e), "exists": False}

    async def run_acceptance_checks(self, stock_code: str):
        """
        运行验收方案中的检查点
        """
        results = {}
        
        # 1. Check Data Ingestion
        results['wencai_stocks'] = await self.verify_data_exists(stock_code, "wencai_stocks")
        results['monitor_list'] = await self.verify_data_exists(stock_code, "monitor_list")
        
        # 2. Check Historical Data
        results['stock_daily'] = await self.verify_data_exists(stock_code, "stock_daily", "vol > 0")
        
        # 3. Check Analysis
        results['baseline'] = await self.verify_data_exists(stock_code, "stock_volume_baseline")
        results['tags'] = await self.verify_data_exists(stock_code, "stock_tag_relations")
        
        # 4. Check Scoring
        results['scores'] = await self.verify_data_exists(stock_code, "stock_score_results")
        
        # 5. Check Alerts
        # results['alerts'] = await self.verify_data_exists(stock_code, "alert_records")
        
        return results
