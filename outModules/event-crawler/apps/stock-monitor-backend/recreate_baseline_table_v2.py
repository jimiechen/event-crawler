
import asyncio
import os
import sys
from sqlalchemy import text
from app.database import db_manager

# SQL to drop the old table
SQL_DROP_TABLE = "DROP TABLE IF EXISTS `stock_volume_baseline`;"

# SQL to create the new table
SQL_CREATE_TABLE = """
CREATE TABLE `stock_volume_baseline` (
  `code` varchar(20) NOT NULL COMMENT '股票代码',
  `last_3x_date` date DEFAULT NULL COMMENT '最近一次3倍量日期',
  `last_3x_close` decimal(20,3) DEFAULT NULL COMMENT '最近一次3倍量收盘价',
  `last_2x_date` date DEFAULT NULL COMMENT '最近一次2倍量日期',
  `last_2x_close` decimal(20,3) DEFAULT NULL COMMENT '最近一次2倍量收盘价',
  
  `last_5d_low_vol_date` date DEFAULT NULL COMMENT '最近一次5日地量日期',
  `last_5d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次5日地量成交量',
  
  `last_10d_low_vol_date` date DEFAULT NULL COMMENT '最近一次10日地量日期',
  `last_10d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次10日地量成交量',
  
  `last_20d_low_vol_date` date DEFAULT NULL COMMENT '最近一次20日地量日期',
  `last_20d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次20日地量成交量',
  
  `last_30d_low_vol_date` date DEFAULT NULL COMMENT '最近一次30日地量日期',
  `last_30d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次30日地量成交量',
  
  `last_60d_low_vol_date` date DEFAULT NULL COMMENT '最近一次60日地量日期',
  `last_60d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次60日地量成交量',
  
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票成交量异动基准表';
"""

async def recreate_table():
    print("Initializing database...")
    await db_manager.initialize()
    print("Dropping and recreating stock_volume_baseline table...")
    session = db_manager.session_factory()
    try:
        await session.execute(text(SQL_DROP_TABLE))
        await session.execute(text(SQL_CREATE_TABLE))
        await session.commit()
        print("Table recreated successfully with new schema.")
    except Exception as e:
        print(f"Error recreating table: {e}")
        await session.rollback()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(recreate_table())
