-- 同花顺股票监控系统数据库表结构设计
-- 数据库：tonghuashun_monitor
-- 字符集：utf8mb4_unicode_ci

USE tonghuashun_monitor;

-- 1. 股票基本信息表
CREATE TABLE IF NOT EXISTS stock_info (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码（如：000001）',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    market VARCHAR(10) NOT NULL COMMENT '市场类型（SZ/SH）',
    industry VARCHAR(100) COMMENT '所属行业',
    sector VARCHAR(100) COMMENT '所属板块',
    listing_date DATE COMMENT '上市日期',
    total_shares BIGINT COMMENT '总股本',
    circulating_shares BIGINT COMMENT '流通股本',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_stock_code (stock_code),
    INDEX idx_market (market),
    INDEX idx_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基本信息表';

-- 2. 股票实时数据表
CREATE TABLE IF NOT EXISTS stock_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    current_price DECIMAL(10,3) NOT NULL COMMENT '当前价格',
    open_price DECIMAL(10,3) COMMENT '开盘价',
    high_price DECIMAL(10,3) COMMENT '最高价',
    low_price DECIMAL(10,3) COMMENT '最低价',
    prev_close DECIMAL(10,3) COMMENT '昨收价',
    change_amount DECIMAL(10,3) COMMENT '涨跌额',
    change_percent DECIMAL(8,4) COMMENT '涨跌幅(%)',
    volume BIGINT COMMENT '成交量（手）',
    turnover DECIMAL(15,2) COMMENT '成交额（元）',
    turnover_rate DECIMAL(8,4) COMMENT '换手率(%)',
    pe_ratio DECIMAL(10,3) COMMENT '市盈率',
    pb_ratio DECIMAL(10,3) COMMENT '市净率',
    market_cap DECIMAL(20,2) COMMENT '总市值（元）',
    circulating_market_cap DECIMAL(20,2) COMMENT '流通市值（元）',
    data_timestamp TIMESTAMP NOT NULL COMMENT '数据时间戳',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_stock_code (stock_code),
    INDEX idx_data_timestamp (data_timestamp),
    INDEX idx_stock_time (stock_code, data_timestamp),
    FOREIGN KEY (stock_code) REFERENCES stock_info(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票实时数据表';

-- 3. 监控股票列表表
CREATE TABLE IF NOT EXISTS monitor_list (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    monitor_type ENUM('realtime', 'daily', 'weekly') DEFAULT 'realtime' COMMENT '监控类型',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用监控（1:启用，0:禁用）',
    alert_rules JSON COMMENT '预警规则配置（JSON格式）',
    last_monitor_time TIMESTAMP NULL COMMENT '最后监控时间',
    monitor_interval INT DEFAULT 60 COMMENT '监控间隔（秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_stock_monitor (stock_code, monitor_type),
    INDEX idx_is_active (is_active),
    INDEX idx_monitor_type (monitor_type),
    FOREIGN KEY (stock_code) REFERENCES stock_info(stock_code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控股票列表表';

-- 4. 数据去重日志表
CREATE TABLE IF NOT EXISTS data_dedup_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    data_hash VARCHAR(64) NOT NULL COMMENT 'SHA256数据哈希值',
    data_type ENUM('stock_data', 'stock_info') NOT NULL COMMENT '数据类型',
    data_timestamp TIMESTAMP NOT NULL COMMENT '数据时间戳',
    source_url VARCHAR(500) COMMENT '数据来源URL',
    raw_data_size INT COMMENT '原始数据大小（字节）',
    is_duplicate TINYINT(1) DEFAULT 0 COMMENT '是否重复数据（1:重复，0:新数据）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_data_hash (data_hash),
    INDEX idx_stock_code (stock_code),
    INDEX idx_data_type (data_type),
    INDEX idx_data_timestamp (data_timestamp),
    INDEX idx_is_duplicate (is_duplicate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据去重日志表';

-- 创建视图：活跃监控股票列表
CREATE OR REPLACE VIEW v_active_monitor_stocks AS
SELECT 
    ml.id,
    ml.stock_code,
    si.stock_name,
    si.market,
    ml.monitor_type,
    ml.monitor_interval,
    ml.last_monitor_time,
    ml.alert_rules
FROM monitor_list ml
INNER JOIN stock_info si ON ml.stock_code = si.stock_code
WHERE ml.is_active = 1
ORDER BY ml.monitor_type, ml.stock_code;

-- 创建视图：股票最新数据（MySQL 5.7兼容版本）
CREATE OR REPLACE VIEW v_latest_stock_data AS
SELECT 
    si.stock_code,
    si.stock_name,
    si.market,
    sd.current_price,
    sd.change_amount,
    sd.change_percent,
    sd.volume,
    sd.turnover,
    sd.market_cap,
    sd.data_timestamp
FROM stock_info si
LEFT JOIN stock_data sd ON si.stock_code = sd.stock_code
WHERE sd.data_timestamp = (
    SELECT MAX(data_timestamp) 
    FROM stock_data sd2 
    WHERE sd2.stock_code = si.stock_code
) OR sd.data_timestamp IS NULL;

-- 插入测试数据
INSERT IGNORE INTO stock_info (stock_code, stock_name, market, industry, sector) VALUES
('000001', '平安银行', 'SZ', '银行', '金融'),
('000002', '万科A', 'SZ', '房地产开发', '房地产'),
('600000', '浦发银行', 'SH', '银行', '金融'),
('600036', '招商银行', 'SH', '银行', '金融'),
('000858', '五粮液', 'SZ', '白酒', '食品饮料');

-- 插入监控列表测试数据
INSERT IGNORE INTO monitor_list (stock_code, monitor_type, monitor_interval) VALUES
('000001', 'realtime', 30),
('000002', 'realtime', 60),
('600000', 'daily', 3600),
('600036', 'realtime', 30),
('000858', 'realtime', 60);

COMMIT;