-- 问财数据抓取功能 - 数据库表结构
-- 创建时间: 2024-12-19
-- 说明: 为问财股票数据抓取功能创建专用表

-- 1. 问财股票数据表
CREATE TABLE IF NOT EXISTS wencai_stocks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    crawl_batch_id BIGINT NOT NULL COMMENT '抓取批次ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    current_price DECIMAL(10,3) COMMENT '当前价格',
    change_percent DECIMAL(8,3) COMMENT '涨跌幅(%)',
    total_market_cap VARCHAR(50) COMMENT '总市值',
    volume VARCHAR(50) COMMENT '成交量',
    turnover VARCHAR(50) COMMENT '成交额',
    circulating_shares VARCHAR(50) COMMENT '流通股本',
    pe_ratio DECIMAL(10,4) COMMENT '市盈率',
    circulating_market_cap VARCHAR(50) COMMENT '流通市值',
    high_price DECIMAL(10,3) COMMENT '最高价',
    low_price DECIMAL(10,3) COMMENT '最低价',
    open_price DECIMAL(10,3) COMMENT '开盘价',
    prev_close DECIMAL(10,3) COMMENT '昨收价',
    turnover_rate DECIMAL(8,4) COMMENT '换手率(%)',
    registered_address TEXT COMMENT '注册地址',
    business_scope TEXT COMMENT '经营范围',
    total_shares VARCHAR(50) COMMENT '总股本',
    industry_classification VARCHAR(200) COMMENT '行业分类',
    board_type VARCHAR(20) COMMENT '板块类型(主板/创业板/科创板等)',
    data_source VARCHAR(50) DEFAULT 'wencai' COMMENT '数据来源',
    raw_data JSON COMMENT '原始HTML数据(可选)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_crawl_batch_id (crawl_batch_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_stock_name (stock_name),
    INDEX idx_current_price (current_price),
    INDEX idx_change_percent (change_percent),
    INDEX idx_created_at (created_at),
    INDEX idx_batch_code (crawl_batch_id, stock_code),
    
    -- 唯一约束：同一批次中的股票代码唯一
    UNIQUE KEY uk_batch_stock (crawl_batch_id, stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财股票数据表';

-- 2. 问财抓取批次表
CREATE TABLE IF NOT EXISTS wencai_crawl_batches (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    batch_id VARCHAR(50) NOT NULL UNIQUE COMMENT '批次ID',
    query_condition TEXT COMMENT '查询条件',
    css_selector VARCHAR(200) DEFAULT '#iwcTableWrapper table' COMMENT 'CSS选择器',
    total_count INT DEFAULT 0 COMMENT '抓取总数',
    success_count INT DEFAULT 0 COMMENT '成功解析数',
    failed_count INT DEFAULT 0 COMMENT '失败数',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '批次状态',
    error_message TEXT COMMENT '错误信息',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration_seconds INT COMMENT '耗时(秒)',
    user_agent VARCHAR(500) COMMENT '用户代理',
    page_url TEXT COMMENT '抓取页面URL',
    created_by VARCHAR(50) DEFAULT 'system' COMMENT '创建者',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财抓取批次表';

-- 3. 问财数据去重表（扩展现有去重机制）
CREATE TABLE IF NOT EXISTS wencai_data_dedup (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    crawl_batch_id BIGINT NOT NULL COMMENT '批次ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    data_hash VARCHAR(64) NOT NULL COMMENT '数据哈希值(SHA256)',
    hash_fields TEXT COMMENT '参与哈希计算的字段',
    is_duplicate BOOLEAN DEFAULT FALSE COMMENT '是否重复',
    original_data JSON COMMENT '原始数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_batch_stock (crawl_batch_id, stock_code),
    INDEX idx_data_hash (data_hash),
    INDEX idx_is_duplicate (is_duplicate),
    INDEX idx_created_at (created_at),
    
    -- 唯一约束
    UNIQUE KEY uk_batch_stock_hash (crawl_batch_id, stock_code, data_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财数据去重表';

-- 4. 创建视图：最新问财股票数据
CREATE OR REPLACE VIEW v_latest_wencai_stocks AS
SELECT 
    ws.*,
    wcb.query_condition,
    wcb.page_url,
    wcb.start_time as batch_start_time
FROM wencai_stocks ws
INNER JOIN (
    SELECT crawl_batch_id, MAX(created_at) as max_created_at
    FROM wencai_stocks
    GROUP BY crawl_batch_id
) latest ON ws.crawl_batch_id = latest.crawl_batch_id
INNER JOIN wencai_crawl_batches wcb ON ws.crawl_batch_id = wcb.id
WHERE wcb.status = 'completed'
ORDER BY ws.created_at DESC;

-- 5. 创建视图：问财抓取统计
CREATE OR REPLACE VIEW v_wencai_crawl_stats AS
SELECT 
    DATE(created_at) as crawl_date,
    COUNT(*) as batch_count,
    SUM(total_count) as total_stocks,
    SUM(success_count) as total_success,
    SUM(failed_count) as total_failed,
    AVG(duration_seconds) as avg_duration,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_batches,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_batches
FROM wencai_crawl_batches
GROUP BY DATE(created_at)
ORDER BY crawl_date DESC;

-- 6. 插入默认配置到系统配置表
INSERT IGNORE INTO system_config (config_key, config_value, description) VALUES
('wencai_css_selector', '#iwcTableWrapper table', '问财表格CSS选择器'),
('wencai_batch_size', '100', '问财单次抓取最大数量'),
('wencai_retry_times', '3', '问财抓取重试次数'),
('wencai_timeout_seconds', '30', '问财抓取超时时间(秒)'),
('wencai_dedup_enabled', 'true', '是否启用问财数据去重'),
('wencai_auto_sync_stock_info', 'true', '是否自动同步到stock_info表');

-- 7. 创建触发器：自动同步到stock_info表
DELIMITER $$

CREATE TRIGGER tr_wencai_sync_stock_info
AFTER INSERT ON wencai_stocks
FOR EACH ROW
BEGIN
    -- 检查是否启用自动同步
    DECLARE sync_enabled VARCHAR(10);
    SELECT config_value INTO sync_enabled 
    FROM system_config 
    WHERE config_key = 'wencai_auto_sync_stock_info';
    
    IF sync_enabled = 'true' THEN
        -- 插入或更新stock_info表
        INSERT INTO stock_info (code, name, market, is_active, created_at, updated_at)
        VALUES (
            NEW.stock_code, 
            NEW.stock_name, 
            CASE 
                WHEN NEW.stock_code LIKE '6%' THEN 'sh'
                WHEN NEW.stock_code LIKE '0%' OR NEW.stock_code LIKE '3%' THEN 'sz'
                ELSE 'unknown'
            END,
            TRUE,
            NOW(),
            NOW()
        )
        ON DUPLICATE KEY UPDATE
            name = NEW.stock_name,
            updated_at = NOW();
    END IF;
END$$

DELIMITER ;

-- 8. 创建存储过程：清理过期问财数据
DELIMITER $$

CREATE PROCEDURE sp_cleanup_wencai_data(IN days_to_keep INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE batch_to_delete VARCHAR(50);
    DECLARE cur CURSOR FOR 
        SELECT batch_id 
        FROM wencai_crawl_batches 
        WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION;
    
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO batch_to_delete;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- 删除相关数据
        DELETE FROM wencai_data_dedup WHERE crawl_batch_id = batch_to_delete;
        DELETE FROM wencai_stocks WHERE crawl_batch_id = batch_to_delete;
        DELETE FROM wencai_crawl_batches WHERE id = batch_to_delete;
        
    END LOOP;
    CLOSE cur;
    
    COMMIT;
    
    SELECT CONCAT('清理完成，删除了 ', ROW_COUNT(), ' 个批次的数据') as result;
END$$

DELIMITER ;