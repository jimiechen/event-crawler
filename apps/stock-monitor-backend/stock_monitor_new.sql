/*
 Navicat Premium Data Transfer

 Source Server         : 127.0.0.1
 Source Server Type    : MySQL
 Source Server Version : 50738
 Source Host           : localhost:3306
 Source Schema         : stock_monitor_new

 Target Server Type    : MySQL
 Target Server Version : 50738
 File Encoding         : 65001

 Date: 11/01/2026 17:44:41
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for alert_record
-- ----------------------------
DROP TABLE IF EXISTS `alert_record`;
CREATE TABLE `alert_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `alert_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提醒类型(Price/Volume)',
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提醒消息',
  `is_sent` tinyint(1) NOT NULL COMMENT '是否已发送',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_alert_type` (`alert_type`),
  KEY `idx_alert_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=762 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提醒记录表';

-- ----------------------------
-- Table structure for analysis_logs
-- ----------------------------
DROP TABLE IF EXISTS `analysis_logs`;
CREATE TABLE `analysis_logs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `trade_date` date NOT NULL,
  `log_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_number` int(11) DEFAULT NULL,
  `rule_content` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vp_action_hint` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `details` json DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code_date_type_rule` (`code`,`trade_date`,`log_type`,`rule_number`),
  KEY `idx_code` (`code`),
  KEY `idx_trade_date` (`trade_date`),
  KEY `idx_type` (`log_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for automation_configs
-- ----------------------------
DROP TABLE IF EXISTS `automation_configs`;
CREATE TABLE `automation_configs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_version` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'APP版本号',
  `device_model` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备型号',
  `resolution` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分辨率 (e.g., 1080x2400)',
  `config_data` json NOT NULL COMMENT '坐标配置 (JSON格式)',
  `is_active` tinyint(1) NOT NULL COMMENT '是否启用',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for automation_logs
-- ----------------------------
DROP TABLE IF EXISTS `automation_logs`;
CREATE TABLE `automation_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` int(11) DEFAULT NULL,
  `device_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `step` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '步骤名称',
  `level` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志级别: INFO, ERROR',
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志内容',
  `screenshot_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '截图存储路径',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `task_id` (`task_id`),
  CONSTRAINT `automation_logs_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `automation_tasks` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for automation_tasks
-- ----------------------------
DROP TABLE IF EXISTS `automation_tasks`;
CREATE TABLE `automation_tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型 (e.g., smart_order)',
  `params` json NOT NULL COMMENT '任务参数',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态: pending, running, success, failed',
  `device_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '执行设备ID',
  `result_data` json DEFAULT NULL COMMENT '执行结果',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for batch_tag_relations
-- ----------------------------
DROP TABLE IF EXISTS `batch_tag_relations`;
CREATE TABLE `batch_tag_relations` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` int(11) NOT NULL COMMENT '批次ID',
  `tag_id` int(11) NOT NULL COMMENT '标签ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_batch_tag` (`batch_id`,`tag_id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_tag_id` (`tag_id`),
  CONSTRAINT `batch_tag_relations_ibfk_1` FOREIGN KEY (`tag_id`) REFERENCES `stock_tags_info` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=511 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='批次标签关联表';

-- ----------------------------
-- Table structure for batch_task_execution_log
-- ----------------------------
DROP TABLE IF EXISTS `batch_task_execution_log`;
CREATE TABLE `batch_task_execution_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `task_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型: csv_sync, tushare_sync, calculate',
  `task_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '执行URL',
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态: pending, running, success, failed',
  `result_message` text COLLATE utf8mb4_unicode_ci COMMENT '执行结果信息',
  `executed_at` datetime DEFAULT NULL COMMENT '执行时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1115 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for chrome_cookies
-- ----------------------------
DROP TABLE IF EXISTS `chrome_cookies`;
CREATE TABLE `chrome_cookies` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `domain` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '域名',
  `cookies_json` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Cookie JSON数据',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `xpath_config` text COLLATE utf8mb4_unicode_ci COMMENT '登录检查XPath配置',
  `is_valid` tinyint(1) DEFAULT '1' COMMENT 'Cookie是否有效',
  `account_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '账号名称/备注',
  `test_url` text COLLATE utf8mb4_unicode_ci COMMENT '测试URL',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'unknown' COMMENT '状态: active, expired, unknown',
  `last_checked_at` datetime DEFAULT NULL COMMENT '上次检查时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `domain` (`domain`)
) ENGINE=InnoDB AUTO_INCREMENT=16066 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for crawler_login_status
-- ----------------------------
DROP TABLE IF EXISTS `crawler_login_status`;
CREATE TABLE `crawler_login_status` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `platform` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台',
  `is_logged_in` tinyint(1) NOT NULL COMMENT '是否已登录',
  `message` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '状态消息',
  `checked_at` datetime NOT NULL COMMENT '检查时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for crawler_results
-- ----------------------------
DROP TABLE IF EXISTS `crawler_results`;
CREATE TABLE `crawler_results` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `platform` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台',
  `target_id` int(11) DEFAULT NULL COMMENT '关联的目标ID',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '内容/标题',
  `author` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作者',
  `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
  `likes` int(11) NOT NULL COMMENT '点赞数',
  `comments` int(11) NOT NULL COMMENT '评论数',
  `shares` int(11) NOT NULL COMMENT '分享数',
  `url` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原文链接',
  `data_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原始数据ID',
  `crawled_at` datetime NOT NULL COMMENT '爬取时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for crawler_targets
-- ----------------------------
DROP TABLE IF EXISTS `crawler_targets`;
CREATE TABLE `crawler_targets` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `platform` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台(bilibili, weibo, etc)',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标名称',
  `url` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标URL或关键词',
  `target_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '类型: url, keyword',
  `is_active` tinyint(1) NOT NULL COMMENT '是否启用',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `last_crawled_at` datetime DEFAULT NULL COMMENT '上次爬取时间',
  `last_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上次状态',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  `xpath_config` text COLLATE utf8mb4_unicode_ci COMMENT 'XPath配置(JSON)',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for data_dedup_log
-- ----------------------------
DROP TABLE IF EXISTS `data_dedup_log`;
CREATE TABLE `data_dedup_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `table_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '表名',
  `data_hash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据哈希值(SHA256)',
  `hash_fields` text COLLATE utf8mb4_unicode_ci COMMENT '参与哈希计算的字段',
  `original_data` json DEFAULT NULL COMMENT '原始数据(可选)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_table_hash` (`table_name`,`data_hash`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据去重日志表';

-- ----------------------------
-- Table structure for expma_history
-- ----------------------------
DROP TABLE IF EXISTS `expma_history`;
CREATE TABLE `expma_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易日期(YYYYMMDD)',
  `close_price` float NOT NULL COMMENT '收盘价',
  `expma_13` float DEFAULT NULL COMMENT 'EXPMA13值',
  `expma_21` float DEFAULT NULL COMMENT 'EXPMA21值',
  `expma_55` float DEFAULT NULL COMMENT 'EXPMA55值',
  `volume` float DEFAULT NULL COMMENT '成交量',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_expma_history_stock_code` (`stock_code`),
  KEY `idx_expma_history_stock_trade_date` (`stock_code`,`trade_date`),
  KEY `ix_expma_history_id` (`id`),
  KEY `idx_expma_history_trade_date` (`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='EXPMA历史数据表';

-- ----------------------------
-- Table structure for expma_monitor
-- ----------------------------
DROP TABLE IF EXISTS `expma_monitor`;
CREATE TABLE `expma_monitor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `stock_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '股票名称',
  `is_active` tinyint(1) NOT NULL COMMENT '是否启用监控',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `stock_code` (`stock_code`),
  KEY `ix_expma_monitor_id` (`id`),
  KEY `idx_expma_monitor_is_active` (`is_active`),
  KEY `idx_expma_monitor_stock_code` (`stock_code`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='EXPMA监控股票表';

-- ----------------------------
-- Table structure for expma_signal
-- ----------------------------
DROP TABLE IF EXISTS `expma_signal`;
CREATE TABLE `expma_signal` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `signal_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '信号类型(breakthrough/breakdown)',
  `signal_date` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '信号日期(YYYYMMDD)',
  `close_price` float NOT NULL COMMENT '收盘价',
  `expma_value` float NOT NULL COMMENT 'EXPMA值',
  `breakthrough_strength` float DEFAULT NULL COMMENT '突破强度(%)',
  `volume` float DEFAULT NULL COMMENT '成交量',
  `change_pct` float DEFAULT NULL COMMENT '涨跌幅(%)',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_expma_signal_signal_date` (`signal_date`),
  KEY `ix_expma_signal_id` (`id`),
  KEY `idx_expma_signal_created_at` (`created_at`),
  KEY `idx_expma_signal_stock_code` (`stock_code`),
  KEY `idx_expma_signal_stock_signal_date` (`stock_code`,`signal_date`),
  KEY `idx_expma_signal_signal_type` (`signal_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='EXPMA突破信号表';

-- ----------------------------
-- Table structure for hidden_concepts
-- ----------------------------
DROP TABLE IF EXISTS `hidden_concepts`;
CREATE TABLE `hidden_concepts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `concept_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `concept_name` (`concept_name`),
  KEY `idx_hidden_concept_name` (`concept_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='隐藏的概念列表';

-- ----------------------------
-- Table structure for monitor_configs
-- ----------------------------
DROP TABLE IF EXISTS `monitor_configs`;
CREATE TABLE `monitor_configs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID',
  `monitor_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '监控类型：price-价格，volume-成交量',
  `condition_type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '条件类型：gt-大于，lt-小于，eq-等于',
  `threshold_value` decimal(15,4) NOT NULL COMMENT '阈值',
  `is_active` tinyint(1) NOT NULL COMMENT '是否激活：1-是，0-否',
  `notification_method` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '通知方式：email,sms,webhook',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_monitor_configs_user_id` (`user_id`),
  KEY `idx_monitor_configs_is_active` (`is_active`),
  KEY `idx_monitor_configs_symbol` (`symbol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控配置表';

-- ----------------------------
-- Table structure for monitor_list
-- ----------------------------
DROP TABLE IF EXISTS `monitor_list`;
CREATE TABLE `monitor_list` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `priority` int(11) DEFAULT '1' COMMENT '监控优先级(1-10)',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否启用监控',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`),
  KEY `idx_priority` (`priority`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控股票列表表';

-- ----------------------------
-- Table structure for monitor_log
-- ----------------------------
DROP TABLE IF EXISTS `monitor_log`;
CREATE TABLE `monitor_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `log_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志类型(monitor/scheduler/error)',
  `log_level` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志级别(INFO/WARNING/ERROR)',
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志消息',
  `details` text COLLATE utf8mb4_unicode_ci COMMENT '详细信息(JSON格式)',
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '相关股票代码',
  `execution_time` float DEFAULT NULL COMMENT '执行时间(秒)',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_monitor_log_log_level` (`log_level`),
  KEY `idx_monitor_log_log_type` (`log_type`),
  KEY `idx_monitor_log_created_at` (`created_at`),
  KEY `idx_monitor_log_stock_code` (`stock_code`),
  KEY `ix_monitor_log_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控日志表';

-- ----------------------------
-- Table structure for monitor_logs
-- ----------------------------
DROP TABLE IF EXISTS `monitor_logs`;
CREATE TABLE `monitor_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `monitor_config_id` int(11) NOT NULL COMMENT '监控配置ID',
  `trigger_time` datetime NOT NULL COMMENT '触发时间',
  `trigger_value` decimal(15,4) NOT NULL COMMENT '触发值',
  `threshold_value` decimal(15,4) NOT NULL COMMENT '阈值',
  `message` text COLLATE utf8mb4_unicode_ci COMMENT '监控消息',
  `notification_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '通知状态：pending,sent,failed',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_monitor_logs_monitor_config_id` (`monitor_config_id`),
  KEY `idx_monitor_logs_symbol` (`symbol`),
  KEY `idx_monitor_logs_trigger_time` (`trigger_time`),
  KEY `idx_monitor_logs_notification_status` (`notification_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控日志表';

-- ----------------------------
-- Table structure for network_data
-- ----------------------------
DROP TABLE IF EXISTS `network_data`;
CREATE TABLE `network_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `url` varchar(2000) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求URL',
  `method` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '请求方法',
  `response_data` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '响应数据(JSON格式)',
  `data_size` int(11) NOT NULL COMMENT '数据大小(字节)',
  `source` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据来源',
  `request_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求ID',
  `user_agent` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理',
  `headers` text COLLATE utf8mb4_unicode_ci COMMENT '请求头(JSON格式)',
  `timestamp` datetime NOT NULL COMMENT '数据时间戳',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Chrome扩展网络数据表';

-- ----------------------------
-- Table structure for operation_logs
-- ----------------------------
DROP TABLE IF EXISTS `operation_logs`;
CREATE TABLE `operation_logs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `operator` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'system' COMMENT '操作人',
  `action` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型(create/update/delete/associate/dissociate)',
  `target_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标类型(tag/relation)',
  `target_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标ID',
  `details` json DEFAULT NULL COMMENT '操作详情(变更前后的值)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_action` (`action`),
  KEY `idx_target_type` (`target_type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=7563 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ----------------------------
-- Table structure for pattern_configs
-- ----------------------------
DROP TABLE IF EXISTS `pattern_configs`;
CREATE TABLE `pattern_configs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pattern_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '形态代码',
  `pattern_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '形态名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `score` int(11) NOT NULL COMMENT '分值',
  `days` int(11) NOT NULL COMMENT '形态天数(1/2/3)',
  `is_enabled` tinyint(1) NOT NULL COMMENT '是否启用',
  `priority` int(11) NOT NULL COMMENT '优先级',
  `conflict_rule` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '冲突处理: add(叠加)/replace(覆盖)',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_pattern_code` (`pattern_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='形态评分配置表';

-- ----------------------------
-- Table structure for pattern_stock_pool
-- ----------------------------
DROP TABLE IF EXISTS `pattern_stock_pool`;
CREATE TABLE `pattern_stock_pool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `stock_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '股票名称',
  `score` int(11) NOT NULL COMMENT '当前评分',
  `patterns` json DEFAULT NULL COMMENT '命中的形态列表',
  `industry` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '行业',
  `concept` text COLLATE utf8mb4_unicode_ci COMMENT '概念',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态: core(核心)/watch(观察)/rejected(淘汰)',
  `last_analyzed_at` datetime DEFAULT NULL COMMENT '最后分析时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_pool_code` (`stock_code`),
  KEY `idx_pool_score` (`score`),
  KEY `idx_pool_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=626 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='缠论量价股票池';

-- ----------------------------
-- Table structure for rule_calculation_log
-- ----------------------------
DROP TABLE IF EXISTS `rule_calculation_log`;
CREATE TABLE `rule_calculation_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `rule_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则名称',
  `is_match` tinyint(1) NOT NULL COMMENT '是否符合规则',
  `details` text COLLATE utf8mb4_unicode_ci COMMENT '计算详情',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_rule_log_created` (`created_at`),
  KEY `idx_rule_log_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=3262 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='规则计算日志表';

-- ----------------------------
-- Table structure for scheduled_task
-- ----------------------------
DROP TABLE IF EXISTS `scheduled_task`;
CREATE TABLE `scheduled_task` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务名称',
  `task_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型(唯一标识): daily_sync, daily_score等',
  `cron_expression` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Cron表达式',
  `is_active` tinyint(1) NOT NULL COMMENT '是否启用',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '任务描述',
  `last_run_at` datetime DEFAULT NULL COMMENT '上次运行时间',
  `last_run_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上次运行状态: success, failed',
  `next_run_at` datetime DEFAULT NULL COMMENT '下次运行时间',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_type` (`task_type`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for scheduler_job
-- ----------------------------
DROP TABLE IF EXISTS `scheduler_job`;
CREATE TABLE `scheduler_job` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `job_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务ID',
  `job_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务名称',
  `job_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型',
  `cron_expression` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Cron表达式',
  `is_active` tinyint(1) NOT NULL COMMENT '是否启用',
  `last_run_time` datetime DEFAULT NULL COMMENT '上次执行时间',
  `next_run_time` datetime DEFAULT NULL COMMENT '下次执行时间',
  `run_count` int(11) NOT NULL COMMENT '执行次数',
  `success_count` int(11) NOT NULL COMMENT '成功次数',
  `error_count` int(11) NOT NULL COMMENT '失败次数',
  `last_error` text COLLATE utf8mb4_unicode_ci COMMENT '最后错误信息',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `job_id` (`job_id`),
  KEY `ix_scheduler_job_id` (`id`),
  KEY `idx_scheduler_job_job_type` (`job_type`),
  KEY `idx_scheduler_job_next_run_time` (`next_run_time`),
  KEY `idx_scheduler_job_is_active` (`is_active`),
  KEY `idx_scheduler_job_job_id` (`job_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时任务表';

-- ----------------------------
-- Table structure for stock_concepts
-- ----------------------------
DROP TABLE IF EXISTS `stock_concepts`;
CREATE TABLE `stock_concepts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `concept_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `crawl_batch_id` int(11) DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_concept_stock_code` (`stock_code`),
  KEY `idx_concept_name` (`concept_name`),
  KEY `idx_concept_batch_id` (`crawl_batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票概念关联表';

-- ----------------------------
-- Table structure for stock_daily
-- ----------------------------
DROP TABLE IF EXISTS `stock_daily`;
CREATE TABLE `stock_daily` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trade_date` date NOT NULL COMMENT '交易日期',
  `open` decimal(10,3) DEFAULT NULL COMMENT '开盘价',
  `close` decimal(10,3) DEFAULT NULL COMMENT '收盘价',
  `high` decimal(10,3) DEFAULT NULL COMMENT '最高价',
  `low` decimal(10,3) DEFAULT NULL COMMENT '最低价',
  `vol` bigint(20) DEFAULT NULL COMMENT '成交量(手)',
  `amount` decimal(20,3) DEFAULT NULL COMMENT '成交额(千元)',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `adj_factor` decimal(10,4) DEFAULT NULL COMMENT '复权因子',
  `turnover_rate` decimal(10,4) DEFAULT NULL COMMENT '换手率(%)',
  `volume_ratio` decimal(10,4) DEFAULT NULL COMMENT '量比',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_daily_code_date` (`code`,`trade_date`),
  KEY `idx_stock_daily_date` (`trade_date`),
  KEY `idx_stock_daily_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=2093176 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票日线数据表';

-- ----------------------------
-- Table structure for stock_daily_temp
-- ----------------------------
DROP TABLE IF EXISTS `stock_daily_temp`;
CREATE TABLE `stock_daily_temp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `open` decimal(10,3) DEFAULT NULL COMMENT '开盘价',
  `close` decimal(10,3) DEFAULT NULL COMMENT '收盘价',
  `high` decimal(10,3) DEFAULT NULL COMMENT '最高价',
  `low` decimal(10,3) DEFAULT NULL COMMENT '最低价',
  `vol` bigint(20) DEFAULT NULL COMMENT '成交量(手)',
  `amount` decimal(20,3) DEFAULT NULL COMMENT '成交额(千元)',
  `turnover_rate` decimal(10,4) DEFAULT NULL COMMENT '换手率(%)',
  `industry` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属行业',
  `concept` text COLLATE utf8mb4_unicode_ci COMMENT '所属概念',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态: pending/passed/rejected',
  `reject_reason` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '拒绝原因',
  `source` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据来源',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_daily_temp_code_date` (`code`,`trade_date`),
  KEY `idx_stock_daily_temp_status` (`status`),
  KEY `idx_stock_daily_temp_created` (`created_at`),
  KEY `idx_stock_daily_temp_date` (`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='临时股票日线数据表';

-- ----------------------------
-- Table structure for stock_data
-- ----------------------------
DROP TABLE IF EXISTS `stock_data`;
CREATE TABLE `stock_data` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票名称',
  `price` decimal(10,3) NOT NULL COMMENT '当前价格',
  `change_amount` decimal(10,3) DEFAULT '0.000' COMMENT '涨跌额',
  `change_percent` decimal(8,3) DEFAULT '0.000' COMMENT '涨跌幅(%)',
  `volume` bigint(20) DEFAULT '0' COMMENT '成交量',
  `turnover` decimal(15,2) DEFAULT '0.00' COMMENT '成交额',
  `high` decimal(10,3) DEFAULT '0.000' COMMENT '最高价',
  `low` decimal(10,3) DEFAULT '0.000' COMMENT '最低价',
  `open_price` decimal(10,3) DEFAULT '0.000' COMMENT '开盘价',
  `prev_close` decimal(10,3) DEFAULT '0.000' COMMENT '昨收价',
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据时间戳',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_code` (`code`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_code_timestamp` (`code`,`timestamp`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票实时数据表';

-- ----------------------------
-- Table structure for stock_info
-- ----------------------------
DROP TABLE IF EXISTS `stock_info`;
CREATE TABLE `stock_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票名称',
  `market` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unknown' COMMENT '市场类型(sh/sz/unknown)',
  `source` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否活跃',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `latest_price` decimal(10,2) DEFAULT NULL COMMENT '最新价格',
  `sync_250d_kline` tinyint(1) DEFAULT '0' COMMENT '是否同步250日K线',
  `sync_incremental` tinyint(1) DEFAULT '0' COMMENT '是否开启增量同步',
  `is_held` tinyint(1) DEFAULT '0' COMMENT '是否持仓',
  `volume_anomaly_score` int(11) DEFAULT '0' COMMENT '成交量异动总分',
  `tdx_plugin_score` int(11) DEFAULT '0' COMMENT 'TDX插件评分',
  `score_update_time` datetime DEFAULT NULL COMMENT '最新评分更新时间',
  `bonus_items` text COLLATE utf8mb4_unicode_ci COMMENT '加分项(JSON)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `idx_code` (`code`),
  KEY `idx_market` (`market`),
  KEY `idx_active` (`is_active`),
  KEY `idx_volume_anomaly_score` (`volume_anomaly_score`),
  KEY `idx_score_update_time` (`score_update_time`)
) ENGINE=InnoDB AUTO_INCREMENT=559 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基本信息表';

-- ----------------------------
-- Table structure for stock_pool
-- ----------------------------
DROP TABLE IF EXISTS `stock_pool`;
CREATE TABLE `stock_pool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '股票名称',
  `source` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '来源(self_selected/wencai)',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_pool_code_source` (`code`,`source`),
  KEY `idx_stock_pool_source` (`source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票池';

-- ----------------------------
-- Table structure for stock_prices
-- ----------------------------
DROP TABLE IF EXISTS `stock_prices`;
CREATE TABLE `stock_prices` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `close_price` decimal(10,3) NOT NULL COMMENT '当前价格',
  `change_rate` decimal(8,4) DEFAULT NULL COMMENT '涨跌幅(%)',
  `volume` bigint(20) DEFAULT NULL COMMENT '成交量',
  `amount` decimal(15,2) DEFAULT NULL COMMENT '成交额',
  `high_price` decimal(10,3) DEFAULT NULL COMMENT '最高价',
  `low_price` decimal(10,3) DEFAULT NULL COMMENT '最低价',
  `open_price` decimal(10,3) DEFAULT NULL COMMENT '开盘价',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `request_timestamp` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求时间戳(来自URL的_参数)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_stock_prices_created_at` (`created_at`),
  KEY `idx_stock_prices_symbol_request_timestamp` (`symbol`,`request_timestamp`),
  KEY `idx_stock_prices_trade_date` (`trade_date`),
  KEY `idx_stock_prices_symbol_date` (`symbol`,`trade_date`),
  KEY `idx_stock_prices_symbol` (`symbol`)
) ENGINE=InnoDB AUTO_INCREMENT=751 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票实时数据表';

-- ----------------------------
-- Table structure for stock_score_result
-- ----------------------------
DROP TABLE IF EXISTS `stock_score_result`;
CREATE TABLE `stock_score_result` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '评分日期',
  `rule_scores` json DEFAULT NULL COMMENT '各规则得分详情',
  `total_score` decimal(10,2) NOT NULL COMMENT '总分',
  `ranking` int(11) DEFAULT NULL COMMENT '排名',
  `pool_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票池类型(self_selected/wencai)',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_score_code_date` (`code`,`trade_date`),
  KEY `idx_stock_score_date` (`trade_date`),
  KEY `idx_stock_score_total` (`total_score`)
) ENGINE=InnoDB AUTO_INCREMENT=156826 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票评分结果表';

-- ----------------------------
-- Table structure for stock_tag_relations
-- ----------------------------
DROP TABLE IF EXISTS `stock_tag_relations`;
CREATE TABLE `stock_tag_relations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `tag_id` int(11) NOT NULL COMMENT '标签ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_tag` (`stock_code`,`tag_id`),
  KEY `idx_stock_code` (`stock_code`),
  KEY `idx_tag_id` (`tag_id`),
  CONSTRAINT `fk_tag_relation_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `stock_tags_info` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票标签关联表';

-- ----------------------------
-- Table structure for stock_tags_info
-- ----------------------------
DROP TABLE IF EXISTS `stock_tags_info`;
CREATE TABLE `stock_tags_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '标签名称',
  `score` decimal(7,2) DEFAULT '0.00' COMMENT '分值',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否软删除',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `tag_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'calculation' COMMENT '标签类型(date/calculation)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_score` (`score`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签信息表';

-- ----------------------------
-- Table structure for stock_tdx_risk
-- ----------------------------
DROP TABLE IF EXISTS `stock_tdx_risk`;
CREATE TABLE `stock_tdx_risk` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `stock_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '股票名称',
  `date` date NOT NULL COMMENT '数据日期',
  `total_score` int(11) DEFAULT NULL COMMENT '总分',
  `total_items` int(11) NOT NULL COMMENT '总检查项',
  `risk_items` int(11) NOT NULL COMMENT '风险项',
  `safe_items` int(11) NOT NULL COMMENT '安全项',
  `highlight_items` int(11) NOT NULL COMMENT '亮点项',
  `raw_json` json DEFAULT NULL COMMENT '原始JSON数据',
  `change_rate` decimal(8,4) DEFAULT NULL COMMENT '涨跌幅(%)',
  `volume` bigint(20) DEFAULT NULL COMMENT '成交量',
  `amount` decimal(15,2) DEFAULT NULL COMMENT '成交额',
  `high_price` decimal(10,3) DEFAULT NULL COMMENT '最高价',
  `low_price` decimal(10,3) DEFAULT NULL COMMENT '最低价',
  `open_price` decimal(10,3) DEFAULT NULL COMMENT '开盘价',
  `trade_date` date NOT NULL COMMENT '数据日期',
  `request_timestamp` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求时间戳(来自URL的_参数)',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tdx_risk_code_date` (`stock_code`,`date`),
  KEY `idx_tdx_risk_date` (`date`),
  KEY `idx_tdx_risk_code` (`stock_code`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通达信股票风险检测数据';

-- ----------------------------
-- Table structure for stock_volume_baseline
-- ----------------------------
DROP TABLE IF EXISTS `stock_volume_baseline`;
CREATE TABLE `stock_volume_baseline` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `last_3x_date` date DEFAULT NULL COMMENT '最近一次3倍量日期',
  `last_3x_close` decimal(20,3) DEFAULT NULL COMMENT '最近一次3倍量收盘价',
  `last_2x_date` date DEFAULT NULL COMMENT '最近一次2倍量日期',
  `last_2x_close` decimal(20,3) DEFAULT NULL COMMENT '最近一次2倍量收盘价',
  `last_5d_low_vol_date` date DEFAULT NULL COMMENT '最近一次5日地量日期',
  `last_5d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次5日地量成交量',
  `last_10d_low_vol_date` date DEFAULT NULL COMMENT '最近一次10日地量日期',
  `last_10d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次10日地量成交量',
  `last_20d_low_vol_date` date DEFAULT NULL COMMENT '最近一次20日地量日期',
  `last_20d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次20日地量成交量',
  `last_30d_low_vol_date` date DEFAULT NULL COMMENT '最近一次30日地量日期',
  `last_30d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次30日地量成交量',
  `last_60d_low_vol_date` date DEFAULT NULL COMMENT '最近一次60日地量日期',
  `last_60d_low_vol` decimal(20,3) DEFAULT NULL COMMENT '最近一次60日地量成交量',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票成交量异动基准表';

-- ----------------------------
-- Table structure for stocks
-- ----------------------------
DROP TABLE IF EXISTS `stocks`;
CREATE TABLE `stocks` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票名称',
  `market` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '市场类型(SH/SZ)',
  `industry` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属行业',
  `list_date` date DEFAULT NULL COMMENT '上市日期',
  `status` tinyint(1) NOT NULL COMMENT '状态：1-正常，0-停牌',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`),
  KEY `idx_symbol` (`symbol`),
  KEY `idx_status` (`status`),
  KEY `idx_market` (`market`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基本信息表';

-- ----------------------------
-- Table structure for sync_task_logs
-- ----------------------------
DROP TABLE IF EXISTS `sync_task_logs`;
CREATE TABLE `sync_task_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `task_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型',
  `batch_id` int(11) DEFAULT NULL COMMENT '关联批次ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务状态',
  `start_time` datetime NOT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `message` text COLLATE utf8mb4_unicode_ci COMMENT '日志详情/错误信息',
  `processed_count` int(11) NOT NULL COMMENT '处理数量',
  `inserted_count` int(11) NOT NULL COMMENT '插入数量',
  `error_count` int(11) NOT NULL COMMENT '错误数量',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for system_config
-- ----------------------------
DROP TABLE IF EXISTS `system_config`;
CREATE TABLE `system_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `config_key` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置键',
  `config_value` text COLLATE utf8mb4_unicode_ci COMMENT '配置值',
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '配置描述',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_key` (`config_key`),
  KEY `idx_key` (`config_key`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ----------------------------
-- Table structure for task_execution_log
-- ----------------------------
DROP TABLE IF EXISTS `task_execution_log`;
CREATE TABLE `task_execution_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务名称',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态(success/failed/running)',
  `message` text COLLATE utf8mb4_unicode_ci COMMENT '执行消息/错误信息',
  `duration` decimal(10,2) DEFAULT NULL COMMENT '耗时(秒)',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '股票代码(可选)',
  PRIMARY KEY (`id`),
  KEY `idx_task_log_created` (`created_at`),
  KEY `idx_task_log_name` (`task_name`)
) ENGINE=InnoDB AUTO_INCREMENT=317 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时任务执行日志';

-- ----------------------------
-- Table structure for tonghuashu_stock
-- ----------------------------
DROP TABLE IF EXISTS `tonghuashu_stock`;
CREATE TABLE `tonghuashu_stock` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stock_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `current_price` decimal(10,3) DEFAULT NULL,
  `record_date` date NOT NULL,
  `tag` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `crawl_url` text COLLATE utf8mb4_unicode_ci,
  `request_timestamp` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ths_tag` (`tag`),
  KEY `idx_ths_stock_code` (`stock_code`),
  KEY `idx_ths_record_date` (`record_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同花顺最小字段表';

-- ----------------------------
-- Table structure for tonghuashun_raw_logs
-- ----------------------------
DROP TABLE IF EXISTS `tonghuashun_raw_logs`;
CREATE TABLE `tonghuashun_raw_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `source` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '数据源标识',
  `url` text COLLATE utf8mb4_unicode_ci COMMENT '原始请求URL',
  `request_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求ID/标识',
  `request_timestamp` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求时间戳',
  `payload_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '载荷类型(string/json/dict/list)',
  `market` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '市场标识，如hs',
  `stock_count` int(11) DEFAULT NULL COMMENT '包含的股票数量',
  `payload` json DEFAULT NULL COMMENT '原始或解析后的JSON载荷',
  `parse_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '解析状态：ok/failed',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT '解析错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ths_raw_logs_source` (`source`),
  KEY `idx_ths_raw_logs_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=9340 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同花顺原始数据日志表';

-- ----------------------------
-- Table structure for tonghuashun_stocks
-- ----------------------------
DROP TABLE IF EXISTS `tonghuashun_stocks`;
CREATE TABLE `tonghuashun_stocks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `current_price` decimal(10,3) NOT NULL,
  `change_percent` decimal(8,4) DEFAULT NULL,
  `volume` bigint(20) DEFAULT NULL,
  `turnover` decimal(15,2) DEFAULT NULL,
  `high` decimal(10,3) DEFAULT NULL,
  `low` decimal(10,3) DEFAULT NULL,
  `open_price` decimal(10,3) DEFAULT NULL,
  `prev_close` decimal(10,3) DEFAULT NULL,
  `timestamp` date NOT NULL,
  `request_timestamp` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `amplitude` decimal(10,3) DEFAULT NULL COMMENT '振幅',
  `turnover_rate` decimal(10,3) DEFAULT NULL COMMENT '换手率',
  `pe_ratio` decimal(10,3) DEFAULT NULL COMMENT '市盈率',
  `market_cap` decimal(20,3) DEFAULT NULL COMMENT '总市值',
  PRIMARY KEY (`id`),
  KEY `idx_ths_created_at` (`created_at`),
  KEY `idx_ths_code` (`code`),
  KEY `idx_ths_timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=11560 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='同花顺标准化股票数据表';

-- ----------------------------
-- Table structure for volume_analysis_result
-- ----------------------------
DROP TABLE IF EXISTS `volume_analysis_result`;
CREATE TABLE `volume_analysis_result` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `analysis_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分析类型',
  `value` decimal(20,3) NOT NULL COMMENT '关键值(价格或成交量)',
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '描述',
  `extra_data` json DEFAULT NULL COMMENT '额外数据',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_unique_analysis` (`code`,`trade_date`,`analysis_type`),
  KEY `idx_vol_analysis_code_type_date` (`code`,`analysis_type`,`trade_date`),
  KEY `idx_vol_analysis_code_date` (`code`,`trade_date`),
  KEY `idx_vol_analysis_type` (`analysis_type`)
) ENGINE=InnoDB AUTO_INCREMENT=24024 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成交量异动分析结果表';

-- ----------------------------
-- Table structure for volume_price_logs
-- ----------------------------
DROP TABLE IF EXISTS `volume_price_logs`;
CREATE TABLE `volume_price_logs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `trade_date` date NOT NULL COMMENT '交易日期',
  `position_label` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '位置标签',
  `volume_status` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '成交量状态',
  `price_status` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '价格状态',
  `volume_price_pattern` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '量价模式',
  `vp_action_hint` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作提示',
  `details` json DEFAULT NULL COMMENT '详情JSON',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code_trade_date` (`code`,`trade_date`),
  KEY `idx_code` (`code`),
  KEY `idx_trade_date` (`trade_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='量价分析日志表';

-- ----------------------------
-- Table structure for wencai_crawl_batches
-- ----------------------------
DROP TABLE IF EXISTS `wencai_crawl_batches`;
CREATE TABLE `wencai_crawl_batches` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '批次ID',
  `batch_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次名称',
  `query_condition` text COLLATE utf8mb4_unicode_ci,
  `crawl_url` text COLLATE utf8mb4_unicode_ci COMMENT '抓取URL',
  `total_records` int(11) DEFAULT '0' COMMENT '总记录数',
  `success_records` int(11) DEFAULT '0' COMMENT '成功记录数',
  `failed_records` int(11) DEFAULT '0' COMMENT '失败记录数',
  `status` enum('pending','processing','completed','failed') COLLATE utf8mb4_unicode_ci DEFAULT 'pending' COMMENT '状态',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT '错误信息',
  `started_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `created_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT 'system' COMMENT '创建者',
  `query_string` text COLLATE utf8mb4_unicode_ci COMMENT '原始查询条件',
  `tags` json DEFAULT NULL COMMENT '解析出的结构化标签',
  `query_date` date DEFAULT NULL COMMENT '查询日期',
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`),
  KEY `idx_started_at` (`started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财抓取批次表';

-- ----------------------------
-- Table structure for wencai_data_dedup
-- ----------------------------
DROP TABLE IF EXISTS `wencai_data_dedup`;
CREATE TABLE `wencai_data_dedup` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `data_hash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据哈希值',
  `crawl_batch_id` bigint(20) NOT NULL COMMENT '抓取批次ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `stock_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '股票名称',
  `current_price` decimal(10,3) DEFAULT NULL COMMENT '当前价格',
  `change_percent` decimal(8,3) DEFAULT NULL COMMENT '涨跌幅(%)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_hash` (`stock_code`,`data_hash`),
  KEY `idx_crawl_batch` (`crawl_batch_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财数据去重表';

-- ----------------------------
-- Table structure for wencai_stocks
-- ----------------------------
DROP TABLE IF EXISTS `wencai_stocks`;
CREATE TABLE `wencai_stocks` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `stock_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票代码',
  `stock_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '股票名称',
  `current_price` decimal(10,3) DEFAULT NULL COMMENT '现价',
  `price_change` decimal(10,3) DEFAULT NULL COMMENT '涨跌额',
  `price_change_percent` decimal(8,3) DEFAULT NULL COMMENT '涨跌幅(%)',
  `volume` bigint(20) DEFAULT NULL COMMENT '成交量',
  `turnover` decimal(15,2) DEFAULT NULL COMMENT '成交额',
  `amplitude` decimal(8,3) DEFAULT NULL COMMENT '振幅(%)',
  `highest_price` decimal(10,3) DEFAULT NULL COMMENT '最高价',
  `lowest_price` decimal(10,3) DEFAULT NULL COMMENT '最低价',
  `opening_price` decimal(10,3) DEFAULT NULL COMMENT '今开',
  `previous_close` decimal(10,3) DEFAULT NULL COMMENT '昨收',
  `volume_ratio` decimal(8,3) DEFAULT NULL COMMENT '量比',
  `turnover_rate` decimal(8,3) DEFAULT NULL COMMENT '换手率(%)',
  `pe_ratio` decimal(10,3) DEFAULT NULL COMMENT '市盈率(动态)',
  `pb_ratio` decimal(10,3) DEFAULT NULL COMMENT '市净率',
  `total_market_value` decimal(20,2) DEFAULT NULL COMMENT '总市值',
  `circulating_market_value` decimal(20,2) DEFAULT NULL COMMENT '流通市值',
  `speed_60_days` decimal(8,3) DEFAULT NULL COMMENT '60日涨跌幅(%)',
  `speed_year_to_date` decimal(8,3) DEFAULT NULL COMMENT '年初至今涨跌幅(%)',
  `company_address` text COLLATE utf8mb4_unicode_ci COMMENT '公司地址',
  `business_scope` text COLLATE utf8mb4_unicode_ci COMMENT '经营范围',
  `crawl_batch_id` bigint(20) NOT NULL COMMENT '抓取批次ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `concept` text COLLATE utf8mb4_unicode_ci COMMENT '所属概念',
  `industry` text COLLATE utf8mb4_unicode_ci COMMENT '所属行业',
  `raw_data` text COLLATE utf8mb4_unicode_ci COMMENT '原始HTML数据',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_batch` (`stock_code`,`crawl_batch_id`),
  KEY `idx_stock_code` (`stock_code`),
  KEY `idx_crawl_batch` (`crawl_batch_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问财股票数据表';

-- ----------------------------
-- View structure for latest_stock_data
-- ----------------------------
DROP VIEW IF EXISTS `latest_stock_data`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `latest_stock_data` AS select `sd`.`id` AS `id`,`sd`.`code` AS `code`,`sd`.`name` AS `name`,`sd`.`price` AS `price`,`sd`.`change_amount` AS `change_amount`,`sd`.`change_percent` AS `change_percent`,`sd`.`volume` AS `volume`,`sd`.`turnover` AS `turnover`,`sd`.`high` AS `high`,`sd`.`low` AS `low`,`sd`.`open_price` AS `open_price`,`sd`.`prev_close` AS `prev_close`,`sd`.`timestamp` AS `timestamp`,`sd`.`created_at` AS `created_at`,`si`.`market` AS `market` from ((`stock_monitor_new`.`stock_data` `sd` join (select `stock_monitor_new`.`stock_data`.`code` AS `code`,max(`stock_monitor_new`.`stock_data`.`timestamp`) AS `max_timestamp` from `stock_monitor_new`.`stock_data` group by `stock_monitor_new`.`stock_data`.`code`) `latest` on(((`sd`.`code` = `latest`.`code`) and (`sd`.`timestamp` = `latest`.`max_timestamp`)))) left join `stock_monitor_new`.`stock_info` `si` on((`sd`.`code` = `si`.`code`)));

-- ----------------------------
-- View structure for monitor_stats
-- ----------------------------
DROP VIEW IF EXISTS `monitor_stats`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `monitor_stats` AS select `ml`.`code` AS `code`,`si`.`name` AS `stock_name`,`si`.`market` AS `market`,`ml`.`priority` AS `priority`,`ml`.`is_active` AS `is_active`,count(`sd`.`id`) AS `data_count`,max(`sd`.`timestamp`) AS `last_update`,avg(`sd`.`price`) AS `avg_price` from ((`monitor_list` `ml` left join `stock_info` `si` on((`ml`.`code` = `si`.`code`))) left join `stock_data` `sd` on((`ml`.`code` = `sd`.`code`))) where (`ml`.`is_active` = TRUE) group by `ml`.`code`,`si`.`name`,`si`.`market`,`ml`.`priority`,`ml`.`is_active`;

-- ----------------------------
-- View structure for v_latest_wencai_stocks
-- ----------------------------
DROP VIEW IF EXISTS `v_latest_wencai_stocks`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_latest_wencai_stocks` AS select `ws`.`id` AS `id`,`ws`.`stock_code` AS `stock_code`,`ws`.`stock_name` AS `stock_name`,`ws`.`current_price` AS `current_price`,`ws`.`price_change` AS `price_change`,`ws`.`price_change_percent` AS `price_change_percent`,`ws`.`volume` AS `volume`,`ws`.`turnover` AS `turnover`,`ws`.`amplitude` AS `amplitude`,`ws`.`highest_price` AS `highest_price`,`ws`.`lowest_price` AS `lowest_price`,`ws`.`opening_price` AS `opening_price`,`ws`.`previous_close` AS `previous_close`,`ws`.`volume_ratio` AS `volume_ratio`,`ws`.`turnover_rate` AS `turnover_rate`,`ws`.`pe_ratio` AS `pe_ratio`,`ws`.`pb_ratio` AS `pb_ratio`,`ws`.`total_market_value` AS `total_market_value`,`ws`.`circulating_market_value` AS `circulating_market_value`,`ws`.`speed_60_days` AS `speed_60_days`,`ws`.`speed_year_to_date` AS `speed_year_to_date`,`ws`.`company_address` AS `company_address`,`ws`.`business_scope` AS `business_scope`,`ws`.`crawl_batch_id` AS `crawl_batch_id`,`ws`.`created_at` AS `created_at`,`ws`.`updated_at` AS `updated_at`,`wcb`.`batch_name` AS `batch_name`,`wcb`.`started_at` AS `batch_time` from ((`stock_monitor_new`.`wencai_stocks` `ws` join (select `stock_monitor_new`.`wencai_stocks`.`stock_code` AS `stock_code`,max(`stock_monitor_new`.`wencai_stocks`.`crawl_batch_id`) AS `latest_batch_id` from `stock_monitor_new`.`wencai_stocks` group by `stock_monitor_new`.`wencai_stocks`.`stock_code`) `latest` on(((`ws`.`stock_code` = `latest`.`stock_code`) and (`ws`.`crawl_batch_id` = `latest`.`latest_batch_id`)))) join `stock_monitor_new`.`wencai_crawl_batches` `wcb` on((`ws`.`crawl_batch_id` = `wcb`.`id`))) where (`wcb`.`status` = 'completed');

-- ----------------------------
-- View structure for v_wencai_crawl_stats
-- ----------------------------
DROP VIEW IF EXISTS `v_wencai_crawl_stats`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `v_wencai_crawl_stats` AS select cast(`wencai_crawl_batches`.`started_at` as date) AS `crawl_date`,count(0) AS `total_batches`,sum(`wencai_crawl_batches`.`total_records`) AS `total_records`,sum(`wencai_crawl_batches`.`success_records`) AS `total_success`,sum(`wencai_crawl_batches`.`failed_records`) AS `total_failed`,avg(((`wencai_crawl_batches`.`success_records` * 100.0) / nullif(`wencai_crawl_batches`.`total_records`,0))) AS `avg_success_rate` from `wencai_crawl_batches` where (`wencai_crawl_batches`.`status` = 'completed') group by cast(`wencai_crawl_batches`.`started_at` as date) order by `crawl_date` desc;

SET FOREIGN_KEY_CHECKS = 1;
