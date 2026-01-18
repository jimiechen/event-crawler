from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

class DataCleaner:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def clear_all_tables(self):
        """
        清空所有业务表数据，保留配置表 (stock_tags_info)
        """
        tables = [
            "wencai_stocks",
            "monitor_list",
            "stock_info",
            "stock_daily",
            "stock_daily_temp",
            "stock_volume_baseline",
            "volume_analysis_result",
            "alert_records",
            "wencai_data_dedup",
            "stock_concepts",
            "wencai_crawl_batches",
            "stock_score_result",
            "rule_calculation_log",
            "task_execution_log",
            "batch_task_execution_log"
        ]

        logger.info("Starting FULL data cleanup...")
        try:
            # Disable FK checks for MySQL/PostgreSQL if needed
            try:
                await self.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            except Exception:
                pass # Ignore if not supported

            for table in tables:
                try:
                    await self.session.execute(text(f"TRUNCATE TABLE {table}"))
                    logger.info(f"Truncated table: {table}")
                except Exception as e:
                    # If TRUNCATE fails (e.g. FK constraints), try DELETE
                    # Also check if table doesn't exist
                    error_msg = str(e)
                    if "1146" in error_msg and "doesn't exist" in error_msg:
                        logger.warning(f"Table {table} does not exist, skipping.")
                        continue
                        
                    logger.warning(f"Truncate failed for {table}, trying DELETE: {e}")
                    try:
                        await self.session.execute(text(f"DELETE FROM {table}"))
                    except Exception as delete_e:
                        error_msg_del = str(delete_e)
                        if "1146" in error_msg_del and "doesn't exist" in error_msg_del:
                            logger.warning(f"Table {table} does not exist, skipping.")
                            continue
                        raise delete_e

            try:
                await self.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            except Exception:
                pass

            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Cleanup failed: {e}")
            raise e
