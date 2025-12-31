import pymysql
from datetime import datetime

# DB Config from .env (reused)
DB_CONFIG = {
    'host': '192.168.1.6',
    'port': 3306,
    'user': 'root',
    'password': '12345678',
    'db': 'stock_monitor_new',
    'charset': 'utf8mb4'
}

SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS `stock_volume_baseline` (
  `code` varchar(20) NOT NULL COMMENT '股票代码',
  `last_3x_date` date DEFAULT NULL COMMENT '最近一次3倍量日期',
  `last_3x_close` decimal(20,3) DEFAULT NULL COMMENT '最近一次3倍量收盘价',
  `last_2x_date` date DEFAULT NULL COMMENT '最近一次2倍量日期',
  `last_2x_close` decimal(20,3) DEFAULT NULL COMMENT '最近一次2倍量收盘价',
  `low_vol_records` json DEFAULT NULL COMMENT '地量记录(5/10/20/30/60日)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票成交量异动基准表';
"""

def create_table():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Creating table stock_volume_baseline...")
        cursor.execute(SQL_CREATE_TABLE)
        conn.commit()
        print("Table created successfully.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_table()
