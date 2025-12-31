ALTER TABLE stock_info ADD COLUMN latest_price DECIMAL(10, 3) COMMENT '最新价格';
ALTER TABLE stock_info ADD COLUMN sync_250d_kline BOOLEAN DEFAULT FALSE COMMENT '是否同步250日K线';
ALTER TABLE stock_info ADD COLUMN incremental_sync BOOLEAN DEFAULT FALSE COMMENT '是否开启增量同步';
ALTER TABLE stock_info ADD COLUMN is_held BOOLEAN DEFAULT FALSE COMMENT '是否持仓';
ALTER TABLE stock_info ADD COLUMN volume_anomaly_score INTEGER DEFAULT 0 COMMENT '成交量异动总分';
ALTER TABLE stock_info ADD COLUMN tdx_plugin_score INTEGER DEFAULT 0 COMMENT 'TDX插件评分';
ALTER TABLE stock_info ADD COLUMN score_update_time DATETIME COMMENT '最新评分更新时间';
ALTER TABLE stock_info ADD COLUMN bonus_items TEXT COMMENT '加分项(JSON)';
