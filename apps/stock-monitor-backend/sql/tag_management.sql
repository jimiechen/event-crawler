-- 标签管理系统数据库表结构
-- 创建时间: 2024-12-09

-- 1. 标签信息表
CREATE TABLE IF NOT EXISTS stock_tags_info (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    name VARCHAR(50) NOT NULL COMMENT '标签名称',
    score DECIMAL(5, 2) DEFAULT 0.00 COMMENT '分值',
    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否软删除',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_name (name),
    INDEX idx_score (score),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签信息表';

-- 2. 股票标签关联表
CREATE TABLE IF NOT EXISTS stock_tag_relations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    tag_id INT NOT NULL COMMENT '标签ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_stock_tag (stock_code, tag_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_tag_id (tag_id),
    CONSTRAINT fk_tag_relation_tag_id FOREIGN KEY (tag_id) REFERENCES stock_tags_info(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票标签关联表';

-- 3. 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    operator VARCHAR(50) DEFAULT 'system' COMMENT '操作人',
    action VARCHAR(50) NOT NULL COMMENT '操作类型(create/update/delete/associate/dissociate)',
    target_type VARCHAR(50) NOT NULL COMMENT '目标类型(tag/relation)',
    target_id VARCHAR(50) NOT NULL COMMENT '目标ID',
    details JSON COMMENT '操作详情(变更前后的值)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_action (action),
    INDEX idx_target_type (target_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';
