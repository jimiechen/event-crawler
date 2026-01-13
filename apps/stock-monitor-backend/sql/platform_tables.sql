-- 平台配置和会话管理数据库迁移脚本
-- 数据库：stock_monitor
-- 字符集：utf8mb4_unicode_ci

USE stock_monitor;

-- 1. 平台配置表
CREATE TABLE IF NOT EXISTS platform_configs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    platform_id VARCHAR(50) UNIQUE NOT NULL COMMENT '平台标识(weibo/bilibili等)',
    name VARCHAR(100) NOT NULL COMMENT '平台名称',
    domain VARCHAR(255) NOT NULL COMMENT 'Cookie域名',
    login_url TEXT COMMENT '登录URL',
    home_url TEXT COMMENT '首页URL',
    verify_api TEXT COMMENT '验证API',
    verify_type VARCHAR(20) DEFAULT 'json' COMMENT '验证类型(json/text)',
    verify_xpath TEXT COMMENT 'XPath配置',
    verify_parser TEXT COMMENT '解析器配置(JSON)',
    icon VARCHAR(50) COMMENT '平台图标(emoji)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_platform_id (platform_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台配置表';

-- 2. 平台会话表
CREATE TABLE IF NOT EXISTS platform_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    platform_id VARCHAR(50) NOT NULL COMMENT '平台标识',
    user_id VARCHAR(100) COMMENT '用户ID/账号标识',
    account_name VARCHAR(100) COMMENT '账号名称/昵称',
    cookies_json TEXT NOT NULL COMMENT 'Cookie JSON数据',
    user_agent VARCHAR(500) COMMENT 'User-Agent',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态(active/expired/unknown)',
    health_score INT DEFAULT 100 COMMENT '健康度评分(0-100)',
    last_verified_at TIMESTAMP NULL COMMENT '最后验证时间',
    last_used_at TIMESTAMP NULL COMMENT '最后使用时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_platform_user (platform_id, user_id),
    INDEX idx_status (status),
    INDEX idx_health_score (health_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台会话表';

-- 3. 初始化平台配置数据
INSERT IGNORE INTO platform_configs (platform_id, name, domain, login_url, home_url, verify_api, verify_type, verify_xpath, verify_parser, icon) VALUES
('weibo', '微博', '.weibo.com', 'https://weibo.com/login.php', 'https://weibo.com', 'https://weibo.com/ajax/profile/info', 'json', NULL, '{"path": "$.data.user.screen_name"}', '🔴'),
('bilibili', 'B站', '.bilibili.com', 'https://passport.bilibili.com/login', 'https://www.bilibili.com', 'https://api.bilibili.com/x/web-interface/nav', 'json', NULL, '{"path": "$.data.uname"}', '📺'),
('douyin', '抖音', '.douyin.com', 'https://www.douyin.com', 'https://www.douyin.com', 'https://www.douyin.com/', 'text', '//script[@id="RENDER_DATA"]', '{"extract": "nickname"}', '🎵'),
('xiaohongshu', '小红书', '.xiaohongshu.com', 'https://www.xiaohongshu.com', 'https://www.xiaohongshu.com', 'https://edith.xiaohongshu.com/api/sns/web/v1/user/me', 'json', NULL, '{"path": "$.data.nickname"}', '📕'),
('okooo', '澳客', '.okooo.com', 'https://www.okooo.com', 'https://www.okooo.com', 'https://www.okooo.com/', 'text', '//*[@class="user_name"]', '{"regex": "class=\\"user_name\\"[^>]*>([^<]+)"}', '🎰'),
('tonghuashun', '同花顺', '10jqka.com.cn', 'https://t.10jqka.com.cn/login', 'https://t.10jqka.com.cn', 'https://t.10jqka.com.cn/newcircle/user/userPersonal', 'json', NULL, '{"path": "$.data.user.name"}', '📈');

COMMIT;
