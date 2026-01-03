-- 股票监控系统数据库初始化脚本

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `stock_monitor` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE `stock_monitor`;

-- 创建股票信息表
CREATE TABLE IF NOT EXISTS `stocks` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `symbol` varchar(20) NOT NULL COMMENT '股票代码',
    `name` varchar(100) NOT NULL COMMENT '股票名称',
    `market` varchar(10) NOT NULL DEFAULT 'SH' COMMENT '市场类型：SH-上海，SZ-深圳',
    `industry` varchar(50) DEFAULT NULL COMMENT '所属行业',
    `list_date` date DEFAULT NULL COMMENT '上市日期',
    `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '状态：1-正常，0-停牌',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_symbol` (`symbol`),
    KEY `idx_market` (`market`),
    KEY `idx_industry` (`industry`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基础信息表';

-- 创建股票价格表
CREATE TABLE IF NOT EXISTS `stock_prices` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `symbol` varchar(20) NOT NULL COMMENT '股票代码',
    `trade_date` date NOT NULL COMMENT '交易日期',
    `open_price` decimal(10,3) DEFAULT NULL COMMENT '开盘价',
    `high_price` decimal(10,3) DEFAULT NULL COMMENT '最高价',
    `low_price` decimal(10,3) DEFAULT NULL COMMENT '最低价',
    `close_price` decimal(10,3) DEFAULT NULL COMMENT '收盘价',
    `volume` bigint(20) DEFAULT NULL COMMENT '成交量',
    `amount` decimal(15,2) DEFAULT NULL COMMENT '成交额',
    `change_rate` decimal(8,4) DEFAULT NULL COMMENT '涨跌幅',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_symbol_date` (`symbol`, `trade_date`),
    KEY `idx_symbol` (`symbol`),
    KEY `idx_trade_date` (`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票价格历史表';

-- 创建监控配置表
CREATE TABLE IF NOT EXISTS `monitor_configs` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `symbol` varchar(20) NOT NULL COMMENT '股票代码',
    `user_id` varchar(50) NOT NULL COMMENT '用户ID',
    `monitor_type` varchar(20) NOT NULL COMMENT '监控类型：price-价格，volume-成交量',
    `condition_type` varchar(10) NOT NULL COMMENT '条件类型：gt-大于，lt-小于，eq-等于',
    `threshold_value` decimal(15,4) NOT NULL COMMENT '阈值',
    `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否激活：1-是，0-否',
    `notification_method` varchar(20) DEFAULT 'email' COMMENT '通知方式：email,sms,webhook',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_symbol` (`symbol`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控配置表';

-- 创建监控日志表
CREATE TABLE IF NOT EXISTS `monitor_logs` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `symbol` varchar(20) NOT NULL COMMENT '股票代码',
    `monitor_config_id` bigint(20) NOT NULL COMMENT '监控配置ID',
    `trigger_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '触发时间',
    `trigger_value` decimal(15,4) NOT NULL COMMENT '触发值',
    `threshold_value` decimal(15,4) NOT NULL COMMENT '阈值',
    `message` text COMMENT '监控消息',
    `notification_status` varchar(20) DEFAULT 'pending' COMMENT '通知状态：pending,sent,failed',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_symbol` (`symbol`),
    KEY `idx_monitor_config_id` (`monitor_config_id`),
    KEY `idx_trigger_time` (`trigger_time`),
    KEY `idx_notification_status` (`notification_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控日志表';

-- 插入一些测试数据
INSERT IGNORE INTO `stocks` (`symbol`, `name`, `market`, `industry`) VALUES
('000001', '平安银行', 'SZ', '银行'),
('000002', '万科A', 'SZ', '房地产'),
('600000', '浦发银行', 'SH', '银行'),
('600036', '招商银行', 'SH', '银行'),
('600519', '贵州茅台', 'SH', '食品饮料');

-- 设置外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 创建用户并授权（如果需要）
-- GRANT ALL PRIVILEGES ON stock_monitor.* TO 'stock_user'@'%';
-- FLUSH PRIVILEGES;