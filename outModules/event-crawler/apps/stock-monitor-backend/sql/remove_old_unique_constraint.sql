-- 删除旧的唯一约束，使用新的基于时间戳的约束
-- 这个脚本将删除基于 symbol + trade_date 的唯一约束
-- 保留基于 symbol + request_timestamp 的新唯一约束

-- 删除旧的唯一约束
ALTER TABLE stock_prices DROP INDEX uk_symbol_date;

-- 验证约束已删除
SHOW INDEX FROM stock_prices;

-- 添加注释说明新的约束策略
ALTER TABLE stock_prices COMMENT = '股票实时数据表 - 使用symbol+request_timestamp作为唯一约束';