-- 修改问财现有表结构，支持通达信数据源
-- 在现有表上添加source字段和其他必要字段

-- ============================================
-- 1. 修改 wencai_crawl_batches 表
-- ============================================

-- 添加 source 字段（如果不存在）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_crawl_batches' 
               AND column_name = 'source');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_crawl_batches ADD COLUMN source VARCHAR(20) DEFAULT "wencai" COMMENT "数据来源(wencai/tdx)"',
    'SELECT "source column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 sector_code 字段（TDX板块代码，如 3BL0325）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_crawl_batches' 
               AND column_name = 'sector_code');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_crawl_batches ADD COLUMN sector_code VARCHAR(20) DEFAULT NULL COMMENT "TDX板块代码(如: 3BL0325)"',
    'SELECT "sector_code column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 query_date 字段（查询日期，用于替代created_at筛选）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_crawl_batches' 
               AND column_name = 'query_date');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_crawl_batches ADD COLUMN query_date DATE DEFAULT NULL COMMENT "查询日期"',
    'SELECT "query_date column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_wencai_batch_source ON wencai_crawl_batches(source);
CREATE INDEX IF NOT EXISTS idx_wencai_batch_sector ON wencai_crawl_batches(sector_code);
CREATE INDEX IF NOT EXISTS idx_wencai_batch_query_date ON wencai_crawl_batches(query_date);

-- ============================================
-- 2. 修改 wencai_stocks 表
-- ============================================

-- 添加 source 字段
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'source');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN source VARCHAR(20) DEFAULT "wencai" COMMENT "数据来源(wencai/tdx)"',
    'SELECT "source column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 change_percent 字段（涨跌幅）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'change_percent');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN change_percent DECIMAL(8, 4) DEFAULT NULL COMMENT "涨跌幅(%)"',
    'SELECT "change_percent column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 volume_ratio 字段（量比）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'volume_ratio');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN volume_ratio DECIMAL(10, 4) DEFAULT NULL COMMENT "成交量比值"',
    'SELECT "volume_ratio column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 turnover 字段（成交额）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'turnover');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN turnover DECIMAL(20, 3) DEFAULT NULL COMMENT "成交额(元)"',
    'SELECT "turnover column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 high_price 字段（最高价）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'high_price');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN high_price DECIMAL(10, 3) DEFAULT NULL COMMENT "最高价"',
    'SELECT "high_price column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 low_price 字段（最低价）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'low_price');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN low_price DECIMAL(10, 3) DEFAULT NULL COMMENT "最低价"',
    'SELECT "low_price column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 open_price 字段（开盘价）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'open_price');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN open_price DECIMAL(10, 3) DEFAULT NULL COMMENT "开盘价"',
    'SELECT "open_price column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 prev_close 字段（昨收价）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'prev_close');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN prev_close DECIMAL(10, 3) DEFAULT NULL COMMENT "昨收价"',
    'SELECT "prev_close column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 is_limit_up 字段（是否涨停）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'is_limit_up');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN is_limit_up TINYINT(1) DEFAULT 0 COMMENT "是否涨停"',
    'SELECT "is_limit_up column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 strategy_name 字段（策略名称）
SET @exist := (SELECT COUNT(*) FROM information_schema.columns 
               WHERE table_name = 'wencai_stocks' 
               AND column_name = 'strategy_name');
               
SET @sql := IF(@exist = 0, 
    'ALTER TABLE wencai_stocks ADD COLUMN strategy_name VARCHAR(50) DEFAULT NULL COMMENT "策略名称"',
    'SELECT "strategy_name column already exists"');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_wencai_source ON wencai_stocks(source);
CREATE INDEX IF NOT EXISTS idx_wencai_change_percent ON wencai_stocks(change_percent);
CREATE INDEX IF NOT EXISTS idx_wencai_volume_ratio ON wencai_stocks(volume_ratio);

-- ============================================
-- 3. 查看修改后的表结构
-- ============================================

-- DESCRIBE wencai_crawl_batches;
-- DESCRIBE wencai_stocks;
