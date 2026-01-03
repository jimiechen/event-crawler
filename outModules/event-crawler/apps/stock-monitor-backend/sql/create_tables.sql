-- 同花顺股票监控系统数据库表结构
-- 创建时间: 2024-12-19

-- 1. 股票基本信息表
CREATE TABLE IF NOT EXISTS stock_info (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '股票代码',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    market VARCHAR(20) NOT NULL DEFAULT 'unknown' COMMENT '市场类型(sh/sz/unknown)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_code (code),
    INDEX idx_market (market),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基本信息表';

-- 2. 股票实时数据表
CREATE TABLE IF NOT EXISTS stock_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    code VARCHAR(20) NOT NULL COMMENT '股票代码',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    price DECIMAL(10,3) NOT NULL COMMENT '当前价格',
    change_amount DECIMAL(10,3) DEFAULT 0 COMMENT '涨跌额',
    change_percent DECIMAL(8,3) DEFAULT 0 COMMENT '涨跌幅(%)',
    volume BIGINT DEFAULT 0 COMMENT '成交量',
    turnover DECIMAL(15,2) DEFAULT 0 COMMENT '成交额',
    high DECIMAL(10,3) DEFAULT 0 COMMENT '最高价',
    low DECIMAL(10,3) DEFAULT 0 COMMENT '最低价',
    open_price DECIMAL(10,3) DEFAULT 0 COMMENT '开盘价',
    prev_close DECIMAL(10,3) DEFAULT 0 COMMENT '昨收价',
    timestamp TIMESTAMP NOT NULL COMMENT '数据时间戳',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_code (code),
    INDEX idx_timestamp (timestamp),
    INDEX idx_code_timestamp (code, timestamp),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票实时数据表';

-- 3. 监控股票列表表
CREATE TABLE IF NOT EXISTS monitor_list (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    code VARCHAR(20) NOT NULL COMMENT '股票代码',
    priority INT DEFAULT 1 COMMENT '监控优先级(1-10)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用监控',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_code (code),
    INDEX idx_priority (priority),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控股票列表表';

-- 4. 数据去重日志表
CREATE TABLE IF NOT EXISTS data_dedup_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    table_name VARCHAR(50) NOT NULL COMMENT '表名',
    data_hash VARCHAR(64) NOT NULL COMMENT '数据哈希值(SHA256)',
    hash_fields TEXT COMMENT '参与哈希计算的字段',
    original_data JSON COMMENT '原始数据(可选)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_table_hash (table_name, data_hash),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据去重日志表';

-- 5. 系统配置表(可选)
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(255) COMMENT '配置描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 插入默认配置
INSERT IGNORE INTO system_config (config_key, config_value, description) VALUES
('monitor_interval', '30', '监控间隔(秒)'),
('max_data_retention_days', '30', '数据保留天数'),
('dedup_cleanup_days', '7', '去重日志清理天数'),
('api_rate_limit', '100', 'API请求频率限制(次/分钟)');

-- 创建视图：最新股票数据
CREATE OR REPLACE VIEW latest_stock_data AS
SELECT 
    sd.*,
    si.market
FROM stock_data sd
INNER JOIN (
    SELECT code, MAX(timestamp) as max_timestamp
    FROM stock_data
    GROUP BY code
) latest ON sd.code = latest.code AND sd.timestamp = latest.max_timestamp
LEFT JOIN stock_info si ON sd.code = si.code;

-- 创建视图：监控股票统计
CREATE OR REPLACE VIEW monitor_stats AS
SELECT 
    ml.code,
    si.name as stock_name,
    si.market,
    ml.priority,
    ml.is_active,
    COUNT(sd.id) as data_count,
    MAX(sd.timestamp) as last_update,
    AVG(sd.price) as avg_price
FROM monitor_list ml
LEFT JOIN stock_info si ON ml.code = si.code
LEFT JOIN stock_data sd ON ml.code = sd.code
WHERE ml.is_active = TRUE
GROUP BY ml.code, si.name, si.market, ml.priority, ml.is_active;

-- 通用分析日志表
CREATE TABLE IF NOT EXISTS analysis_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    log_type VARCHAR(50) NOT NULL,
    rule_number INT NULL,
    rule_content VARCHAR(255) NULL,
    vp_action_hint VARCHAR(50) NULL,
    details JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code_date_type_rule (code, trade_date, log_type, rule_number),
    INDEX idx_code (code),
    INDEX idx_trade_date (trade_date),
    INDEX idx_type (log_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 量价分析日志表
CREATE TABLE IF NOT EXISTS volume_price_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    code VARCHAR(20) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    position_label VARCHAR(10) COMMENT '位置标签',
    volume_status VARCHAR(10) COMMENT '成交量状态',
    price_status VARCHAR(10) COMMENT '价格状态',
    volume_price_pattern VARCHAR(20) COMMENT '量价模式',
    vp_action_hint VARCHAR(50) COMMENT '操作提示',
    details JSON COMMENT '详情JSON',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_code_trade_date (code, trade_date),
    INDEX idx_code (code),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='量价分析日志表';
