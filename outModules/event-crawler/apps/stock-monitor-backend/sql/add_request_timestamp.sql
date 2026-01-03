-- 添加request_timestamp字段和复合唯一索引
-- 创建时间: 2024-12-19
-- 说明: 为股票数据表添加请求时间戳字段，用于与股票代码组成复合唯一索引

-- 1. 添加request_timestamp字段
ALTER TABLE stock_prices 
ADD COLUMN request_timestamp VARCHAR(50) NULL COMMENT '请求时间戳(来自URL的_参数)';

-- 2. 添加索引
ALTER TABLE stock_prices 
ADD INDEX idx_stock_prices_symbol_request_timestamp (symbol, request_timestamp);

-- 3. 添加复合唯一索引 (股票代码 + 请求时间戳)
-- 注意：由于现有数据可能有重复，先检查数据
-- 如果有重复数据，需要先清理
ALTER TABLE stock_prices 
ADD CONSTRAINT uk_stock_symbol_request_timestamp 
UNIQUE (symbol, request_timestamp);

-- 4. 查看表结构确认修改
DESCRIBE stock_prices;

-- 5. 查看索引确认
SHOW INDEX FROM stock_prices;