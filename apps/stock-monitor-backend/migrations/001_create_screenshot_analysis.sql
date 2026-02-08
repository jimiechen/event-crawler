-- 截图分析记录表
-- 支持三龙聚首指标、K/D信号、主力控盘识别
-- 创建时间: 2026-02-04

CREATE TABLE IF NOT EXISTS screenshot_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    task_id VARCHAR(50) NOT NULL COMMENT '任务ID',
    batch_id VARCHAR(50) COMMENT '批次ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) COMMENT '股票名称',
    industry VARCHAR(50) COMMENT '所属行业',
    screenshot_type VARCHAR(20) DEFAULT 'tlby' COMMENT '截图类型: tlby=天龙博弈日K, fenxi=分时图, kline=普通K线',
    image_data LONGTEXT NOT NULL COMMENT 'Base64图片数据',
    image_format VARCHAR(10) DEFAULT 'png' COMMENT '图片格式: png/jpg/webp',
    image_size INT DEFAULT 0 COMMENT '图片大小(字节)',
    source_ip VARCHAR(50) COMMENT '来源IP',
    agent_id VARCHAR(50) COMMENT 'Agent标识',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending=待分析, analyzing=分析中, completed=已完成, failed=失败',

    -- AI识别基础数据
    ai_price DECIMAL(10, 3) COMMENT 'AI识别价格',
    ai_change_percent DECIMAL(8, 4) COMMENT 'AI识别涨跌幅(%)',
    ai_volume BIGINT COMMENT 'AI识别成交量',
    ai_amount DECIMAL(15, 2) COMMENT 'AI识别成交额',

    -- 三龙聚首指标
    sanlong_trend_alert INT COMMENT '趋势警戒 0/1',
    sanlong_volume_alert INT COMMENT '量能警戒 0/1',
    sanlong_mid_alert INT COMMENT '中期警戒 0/1',
    sanlong_short_alert INT COMMENT '短期警戒 0/1',
    sanlong_alert_count INT COMMENT '亮灯数量0-4',
    sanlong_all_red BOOLEAN COMMENT '是否全红警戒',

    -- K/D信号
    has_k_signal_today BOOLEAN COMMENT '今天是否有K信号(蓝色K图标)',
    has_d_signal_today BOOLEAN COMMENT '今天是否有D信号(黄色房子图标)',
    k_signal_count INT COMMENT 'K信号数量',
    d_signal_count INT COMMENT 'D信号数量',

    -- 形态识别
    detected_pattern VARCHAR(50) COMMENT '识别形态: 天龙博弈/天量博弈等',
    pattern_confidence DECIMAL(3, 2) COMMENT '形态置信度 0-1',

    -- 主力控盘数据(分时图)
    main_force_buy_ratio DECIMAL(5, 2) COMMENT '主力买入占比(%)',
    main_force_sell_ratio DECIMAL(5, 2) COMMENT '主力卖出占比(%)',
    retail_buy_ratio DECIMAL(5, 2) COMMENT '散户买入占比(%)',
    retail_sell_ratio DECIMAL(5, 2) COMMENT '散户卖出占比(%)',

    -- AI结果
    ai_result JSON COMMENT 'AI完整识别结果(JSON)',
    ai_model VARCHAR(50) COMMENT 'AI模型: kimi-k2.5/gemini-3-pro',
    ai_analysis_text TEXT COMMENT 'AI分析文本',

    -- 数据比对结果
    verification_result JSON COMMENT '数据比对结果(JSON)',
    is_data_match BOOLEAN COMMENT '数据是否匹配',
    match_confidence DECIMAL(3, 2) COMMENT '匹配置信度 0-1',

    -- 错误信息
    error_message TEXT COMMENT '错误信息',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    analyzed_at DATETIME COMMENT '分析完成时间',
    callback_sent_at DATETIME COMMENT '回调发送时间',

    -- 索引
    INDEX idx_screenshot_stock_code (stock_code),
    INDEX idx_screenshot_task_id (task_id),
    INDEX idx_screenshot_status (status),
    INDEX idx_screenshot_pattern (detected_pattern),
    INDEX idx_screenshot_created_at (created_at),
    INDEX idx_screenshot_batch_id (batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票截图分析记录表';
