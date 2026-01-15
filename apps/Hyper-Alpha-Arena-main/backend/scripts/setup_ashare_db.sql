-- AShare Adapter Requirements
-- Based on apps/Hyper-Alpha-Arena-main/backend/adapters/ashare_adapter.py

CREATE TABLE IF NOT EXISTS stock_info (
    code VARCHAR(20) NOT NULL PRIMARY KEY COMMENT '股票代码',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    market VARCHAR(20) DEFAULT 'unknown' COMMENT '市场类型',
    volume_anomaly_score INT DEFAULT 0 COMMENT '成交量异动总分',
    tdx_plugin_score INT DEFAULT 0 COMMENT 'TDX插件评分',
    bonus_items TEXT COMMENT '加分项(JSON)',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    close_price DECIMAL(10, 3) NOT NULL COMMENT '收盘价',
    change_rate DECIMAL(8, 4) DEFAULT 0 COMMENT '涨跌幅',
    volume BIGINT DEFAULT 0 COMMENT '成交量',
    amount DECIMAL(15, 2) DEFAULT 0 COMMENT '成交额',
    trade_date DATE NOT NULL COMMENT '交易日期',
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS stock_tdx_risk (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    date DATE NOT NULL COMMENT '数据日期',
    total_score INT DEFAULT 0 COMMENT '总分',
    risk_items INT DEFAULT 0 COMMENT '风险项',
    safe_items INT DEFAULT 0 COMMENT '安全项',
    highlight_items INT DEFAULT 0 COMMENT '亮点项',
    raw_json JSON COMMENT '原始JSON数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_code (stock_code),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert some mock data for testing
INSERT IGNORE INTO stock_info (code, name, market, volume_anomaly_score, tdx_plugin_score, bonus_items) VALUES
('000001', '平安银行', 'SZ', 10, 85, '["核心资产", "低估值"]'),
('600519', '贵州茅台', 'SH', 5, 95, '["白酒龙头", "高股息"]');

INSERT INTO stock_prices (symbol, close_price, change_rate, volume, amount, trade_date) VALUES
('000001', 10.50, 1.25, 1000000, 10500000.00, CURDATE()),
('600519', 1800.00, -0.50, 50000, 90000000.00, CURDATE());

INSERT INTO stock_tdx_risk (stock_code, date, total_score, risk_items, safe_items, highlight_items, raw_json) VALUES
('000001', CURDATE(), 95, 0, 5, 2, '{"tags": ["绩优股", "大盘股"]}'),
('600519', CURDATE(), 90, 1, 4, 3, '{"tags": ["高价股", "消费"]}');
