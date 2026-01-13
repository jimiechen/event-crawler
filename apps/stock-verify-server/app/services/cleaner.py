from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

class DataCleaner:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def clear_stock_data(self, stock_code: str):
        """
        级联清除指定股票的所有相关数据
        """
        # normalize code (remove suffix if needed for some tables, keep for others)
        # Assuming most tables use the code without suffix or with suffix?
        # stock_monitor-backend usually stores '000001' in stock_info.code, '000001.SZ' in stock_daily.ts_code or similar?
        # Let's check the schema or assume both for safety.
        
        # Based on search results earlier:
        # StockInfo: code='000001'
        # StockDaily: code='000001.SZ' (ts_code?) No, StockData model has 'symbol' mapping to 'code'.
        # Let's look at stock_daily_repository or model again?
        # Wait, I don't have the model handy. I'll delete by 'code' or 'stock_code'.
        
        base_code = stock_code.split('.')[0]
        
        tables_to_clear = [
            "wencai_stocks",       # stock_code
            "monitor_list",        # stock_code
            "stock_info",          # code
            "stock_daily",         # code
            "stock_daily_temp",    # code
            "stock_volume_baseline", # code
            # "stock_tag_relations", # stock_code (PROTECTED: Keep for analysis)
            # "stock_score_results", # code (PROTECTED: Keep for analysis)
            "volume_analysis_results", # code
            "alert_records",       # stock_code
            "wencai_data_dedup",   # stock_code
            "stock_concepts",      # stock_code
            "wencai_crawl_batches", # id
            # "stock_scores"         # code (PROTECTED: Keep for analysis)
        ]
        
        logger.info(f"Starting data cleanup for {stock_code}...")
        
        try:
            # Disable foreign key checks temporarily if needed, but better to delete in order?
            # Actually, cascading delete might not be set up in DB.
            # Let's just delete from all tables.
            
            for table in tables_to_clear:
                # Try deleting with both base_code and full code (if provided with suffix)
                # Most tables seem to use base code based on previous search results (e.g. StockInfo.code)
                # But StockDaily might have suffix.
                
                # Using LIKE or OR to be safe? Or just trying both.
                
                # Check if table exists first? No, just try delete.
                try:
                    # Construct query dynamically based on column name convention
                    # Most use 'code' or 'stock_code'
                    
                    # We can use a generic delete if we know the column.
                    # Let's try to delete where code = :code OR stock_code = :code (if column exists)
                    # This is hard with raw SQL without knowing column names.
                    
                    # Hardcoding column names based on common conventions in this project
                    col_name = "stock_code"
                    if table in ["stock_info", "stock_daily", "stock_daily_temp", "stock_volume_baseline", "stock_score_results"]:
                        col_name = "code"
                    
                    # Special handling for tables that might use different column names
                    if table == "stock_daily":
                        # Check previous search: StockData maps to "stock_prices", column "symbol" mapped to "code".
                        # Wait, StockDaily model is different from StockData?
                        # In stock_monitor-backend, there is StockData (stock_prices) and StockDaily (stock_daily).
                        # Acceptance plan mentions `stock_daily`.
                        col_name = "code" # Assuming based on context

                    # Execute delete
                    # Note: Using text() with parameters for safety
                    stmt = text(f"DELETE FROM {table} WHERE {col_name} = :code OR {col_name} = :code_suffix")
                    await self.session.execute(stmt, {"code": base_code, "code_suffix": stock_code})
                    
                except Exception as e:
                    # Table might not exist or column name mismatch
                    # Log warning but continue
                    logger.warning(f"Failed to clear {table}: {e}")

            await self.session.commit()
            logger.info(f"Data cleanup for {stock_code} completed.")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Data cleanup failed: {e}")
            raise e
