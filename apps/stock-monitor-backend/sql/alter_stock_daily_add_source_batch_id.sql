-- 扩展stock_daily表，添加source_batch_id字段
-- 用于关联TDX选股批次

ALTER TABLE stock_daily 
ADD COLUMN source_batch_id INT NULL COMMENT '来源TDX选股批次ID';

-- 添加索引以优化查询性能
CREATE INDEX idx_stock_daily_source_batch ON stock_daily(source_batch_id);
