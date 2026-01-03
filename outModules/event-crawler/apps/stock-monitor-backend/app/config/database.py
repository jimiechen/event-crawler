#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置模块
定义数据库连接参数和配置选项
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

@dataclass
class DatabaseConfig:
    """数据库配置类"""
    
    # 数据库类型
    db_type: str = "mysql"  # mysql 或 sqlite
    
    # 基本连接参数
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "stock_monitor"
    charset: str = "utf8mb4"
    
    # 连接池配置
    min_size: int = 5
    max_size: int = 20
    pool_recycle: int = 3600  # 连接回收时间（秒）
    pool_timeout: int = 30    # 获取连接超时时间（秒）
    
    # 连接超时配置
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30
    
    # 重连配置
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 3
    reconnect_delay: int = 1
    max_retries: int = 3      # 最大重试次数
    retry_delay: int = 1      # 重试延迟（秒）
    
    # SSL配置
    use_ssl: bool = False
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理，从环境变量读取配置"""
        # 从环境变量读取配置
        self.db_type = os.getenv("DB_TYPE", self.db_type)
        self.host = os.getenv("DB_HOST", self.host)
        self.port = int(os.getenv("DB_PORT", self.port))
        self.user = os.getenv("DB_USER", self.user)
        self.password = os.getenv("DB_PASSWORD", self.password)
        self.database = os.getenv("DB_DATABASE", self.database)
        self.charset = os.getenv("DB_CHARSET", self.charset)
        
        # 连接池配置
        self.min_size = int(os.getenv("DB_MIN_SIZE", self.min_size))
        self.max_size = int(os.getenv("DB_MAX_SIZE", self.max_size))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", self.pool_recycle))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", self.pool_timeout))
        
        # 超时配置
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", self.connect_timeout))
        self.read_timeout = int(os.getenv("DB_READ_TIMEOUT", self.read_timeout))
        self.write_timeout = int(os.getenv("DB_WRITE_TIMEOUT", self.write_timeout))
        
        # 重连配置
        self.auto_reconnect = os.getenv("DB_AUTO_RECONNECT", "true").lower() == "true"
        self.max_reconnect_attempts = int(os.getenv("DB_MAX_RECONNECT_ATTEMPTS", self.max_reconnect_attempts))
        self.reconnect_delay = int(os.getenv("DB_RECONNECT_DELAY", self.reconnect_delay))
        self.max_retries = int(os.getenv("DB_MAX_RETRIES", self.max_retries))
        self.retry_delay = int(os.getenv("DB_RETRY_DELAY", self.retry_delay))
        
        # SSL配置
        self.use_ssl = os.getenv("DB_USE_SSL", "false").lower() == "true"
        self.ssl_ca = os.getenv("DB_SSL_CA")
        self.ssl_cert = os.getenv("DB_SSL_CERT")
        self.ssl_key = os.getenv("DB_SSL_KEY")
    
    def get_connection_url(self) -> str:
        """获取数据库连接URL"""
        if self.db_type.lower() == "sqlite":
            return f"sqlite:///{self.database}"
        else:
            return f"mysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_connection_params(self) -> dict:
        """获取连接参数字典"""
        params = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'db': self.database,
            'charset': self.charset,
            'connect_timeout': self.connect_timeout,
            'autocommit': True,
            'echo': False
        }
        
        # SSL配置
        if self.use_ssl:
            ssl_context = {}
            if self.ssl_ca:
                ssl_context['ca'] = self.ssl_ca
            if self.ssl_cert:
                ssl_context['cert'] = self.ssl_cert
            if self.ssl_key:
                ssl_context['key'] = self.ssl_key
            
            if ssl_context:
                params['ssl'] = ssl_context
        
        return params
    
    def validate(self) -> bool:
        """验证配置参数"""
        if not self.host:
            raise ValueError("数据库主机不能为空")
        
        if not (1 <= self.port <= 65535):
            raise ValueError("数据库端口必须在1-65535之间")
        
        if not self.user:
            raise ValueError("数据库用户名不能为空")
        
        if not self.database:
            raise ValueError("数据库名不能为空")
        
        if self.min_size <= 0 or self.max_size <= 0:
            raise ValueError("连接池大小必须大于0")
        
        if self.min_size > self.max_size:
            raise ValueError("最小连接数不能大于最大连接数")
        
        if self.connect_timeout <= 0:
            raise ValueError("连接超时时间必须大于0")
        
        return True
    
    def __str__(self) -> str:
        """字符串表示（隐藏密码）"""
        return f"DatabaseConfig(host={self.host}, port={self.port}, user={self.user}, database={self.database})"

# 默认配置实例
default_config = DatabaseConfig()

# 开发环境配置
dev_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="stock_monitor_dev",
    min_size=2,
    max_size=10
)

# 测试环境配置
test_config = DatabaseConfig(
    host="localhost",
    port=3306,
    user="test",
    password="test",
    database="stock_monitor_test",
    min_size=1,
    max_size=5
)

# 生产环境配置
prod_config = DatabaseConfig(
    host="prod-db-host",
    port=3306,
    user="prod_user",
    password="prod_password",
    database="stock_monitor_prod",
    min_size=10,
    max_size=50,
    use_ssl=True
)

def get_config(env: str = "dev") -> DatabaseConfig:
    """根据环境获取配置"""
    return DatabaseConfig()
