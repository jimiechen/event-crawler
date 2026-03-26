-- TDX选股结果表迁移脚本
-- 创建tdx_selection_result和tdx_selection_batch表
-- 用于存储通达信三倍量+涨停选股结果，与问财来源区分

-- 创建通达信选股结果表
CREATE TABLE IF NOT EXISTS tdx_selection_result (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) DEFAULT NULL COMMENT '股票名称',
    trade_date DATE NOT NULL COMMENT '选股日期',
    sector_code VARCHAR(20) NOT NULL COMMENT '板块代码(如: 3BL0325)',
    sector_name VARCHAR(100) DEFAULT NULL COMMENT '板块名称',
    
    -- 价格数据
    open_price DECIMAL(10, 3) DEFAULT NULL COMMENT '开盘价',
    close_price DECIMAL(10, 3) DEFAULT NULL COMMENT '收盘价',
    high_price DECIMAL(10, 3) DEFAULT NULL COMMENT '最高价',
    low_price DECIMAL(10, 3) DEFAULT NULL COMMENT '最低价',
    prev_close DECIMAL(10, 3) DEFAULT NULL COMMENT '昨收价',
    
    -- 成交量数据
    volume BIGINT DEFAULT NULL COMMENT '成交量(手)',
    prev_volume BIGINT DEFAULT NULL COMMENT '前一日成交量(手)',
    volume_ratio DECIMAL(10, 4) DEFAULT NULL COMMENT '成交量比值(当日/前日)',
    amount DECIMAL(20, 3) DEFAULT NULL COMMENT '成交额(千元)',
    
    -- 涨跌幅
    change_percent DECIMAL(8, 4) DEFAULT NULL COMMENT '涨跌幅(%)',
    limit_up_price DECIMAL(10, 3) DEFAULT NULL COMMENT '涨停价',
    is_limit_up TINYINT(1) DEFAULT 0 COMMENT '是否涨停',
    
    -- 策略标记
    strategy_name VARCHAR(50) DEFAULT '3x_volume_limit_up' COMMENT '策略名称',
    
    -- 数据来源标记 - 区分TDX和问财
    source VARCHAR(20) DEFAULT 'tdx' COMMENT '数据来源(tdx/wencai)',
    
    -- 截图路径
    screenshot_path VARCHAR(500) DEFAULT NULL COMMENT '截图文件路径',
    
    -- 飞书同步状态
    feishu_synced TINYINT(1) DEFAULT 0 COMMENT '是否已同步到飞书',
    feishu_sync_time DATETIME DEFAULT NULL COMMENT '飞书同步时间',
    feishu_record_id VARCHAR(100) DEFAULT NULL COMMENT '飞书多维表格记录ID',
    
    -- 扩展数据
    extra_data JSON DEFAULT NULL COMMENT '扩展数据(JSON格式)',
    
    -- 备注
    remark TEXT DEFAULT NULL COMMENT '备注',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一约束和索引
    UNIQUE KEY uk_tdx_selection_code_date (stock_code, trade_date),
    INDEX idx_tdx_selection_date (trade_date),
    INDEX idx_tdx_selection_code (stock_code),
    INDEX idx_tdx_selection_sector (sector_code),
    INDEX idx_tdx_selection_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通达信选股结果表 - 三倍量+涨停策略';

-- 创建通达信选股批次表
CREATE TABLE IF NOT EXISTS tdx_selection_batch (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    batch_id VARCHAR(50) NOT NULL UNIQUE COMMENT '批次ID',
    trade_date DATE NOT NULL COMMENT '选股日期',
    sector_code VARCHAR(20) NOT NULL COMMENT '板块代码',
    sector_name VARCHAR(100) DEFAULT NULL COMMENT '板块名称',
    strategy_name VARCHAR(50) DEFAULT '3x_volume_limit_up' COMMENT '策略名称',
    
    total_stocks INT DEFAULT 0 COMMENT '选股总数',
    limit_up_count INT DEFAULT 0 COMMENT '涨停股票数',
    high_volume_count INT DEFAULT 0 COMMENT '高成交量股票数',
    
    -- 执行状态
    status VARCHAR(20) DEFAULT 'running' COMMENT '状态: pending/running/completed/failed',
    
    -- 各阶段状态
    data_sync_status VARCHAR(20) DEFAULT 'pending' COMMENT '数据同步状态',
    selection_status VARCHAR(20) DEFAULT 'pending' COMMENT '选股状态',
    screenshot_status VARCHAR(20) DEFAULT 'pending' COMMENT '截图状态',
    feishu_sync_status VARCHAR(20) DEFAULT 'pending' COMMENT '飞书同步状态',
    
    -- 时间记录
    started_at DATETIME DEFAULT NULL COMMENT '开始时间',
    completed_at DATETIME DEFAULT NULL COMMENT '完成时间',
    duration DECIMAL(10, 2) DEFAULT NULL COMMENT '耗时(秒)',
    
    -- 错误信息
    error_message TEXT DEFAULT NULL COMMENT '错误信息',
    
    -- 数据来源
    source VARCHAR(20) DEFAULT 'tdx' COMMENT '数据来源(tdx/wencai)',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_tdx_batch_date (trade_date),
    INDEX idx_tdx_batch_sector (sector_code),
    INDEX idx_tdx_batch_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通达信选股批次表';

-- 添加表注释
ALTER TABLE tdx_selection_result COMMENT = '通达信选股结果表 - 三倍量+涨停策略';
ALTER TABLE tdx_selection_batch COMMENT = '通达信选股批次表';

-- 查看表结构
-- DESCRIBE tdx_selection_result;
-- DESCRIBE tdx_selection_batch;
