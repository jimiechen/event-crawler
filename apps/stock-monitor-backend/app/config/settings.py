#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置设置
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置设置"""
    
    # 基础应用信息
    app_name: str = Field(default="Stock Monitor Backend", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    app_debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="运行环境")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    workers: int = Field(default=5, description="工作进程数")
    
    # 数据库配置
    database_url: Optional[str] = Field(default=None, description="数据库连接URL")
    db_host: str = Field(default="localhost", description="数据库主机")
    db_port: int = Field(default=3306, description="数据库端口")

    # Tushare配置
    tushare_token: Optional[str] = Field(default=None, description="Tushare API Token")
    tushare_incremental_start_date: str = Field(default="2025-12-22", description="Tushare增量同步默认起始日期")
    
    # Pathway配置
    pathway_enabled: bool = Field(default=False, description="是否启用Pathway引擎")
    pathway_csv_path: str = Field(default="/Users/mac/Downloads/daily", description="Pathway CSV路径")
    pathway_snapshot_dir: str = Field(default="./data/pathway_snapshots", description="Pathway快照目录")
    
    # CSV Data Path
    csv_data_path_stock_daily: str = Field(default="/Volumes/MacintoshHD/data/daily", description="股票日线数据CSV存储路径")

    db_user: str = Field(default="root", description="数据库用户名")
    db_password: str = Field(default="", description="数据库密码")
    db_database: str = Field(default="stock_monitor", description="数据库名称")
    db_charset: str = Field(default="utf8mb4", description="数据库字符集")
    db_echo: bool = Field(default=False, description="是否打印SQL语句")
    
    # 数据库连接池配置
    db_min_size: int = Field(default=2, description="连接池最小连接数")
    db_max_size: int = Field(default=10, description="连接池最大连接数")
    db_pool_recycle: int = Field(default=3600, description="连接回收时间(秒)")
    db_pool_timeout: int = Field(default=30, description="连接超时时间(秒)")
    
    # 数据库重试配置
    db_max_retries: int = Field(default=3, description="最大重试次数")
    db_retry_delay: int = Field(default=1, description="重试延迟(秒)")
    
    # Redis配置（可选）
    redis_url: Optional[str] = Field(default=None, description="Redis连接URL")
    redis_host: str = Field(default="localhost", description="Redis主机")
    redis_port: int = Field(default=6379, description="Redis端口")
    redis_db: int = Field(default=0, description="Redis数据库编号")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="logs/app.log", description="日志文件路径")
    log_rotation: str = Field(default="100 MB", description="日志轮转大小")
    log_retention: str = Field(default="30 days", description="日志保留时间")
    log_compression: str = Field(default="gz", description="日志压缩格式")
    
    # CORS配置
    cors_origins: List[str] = Field(default=["http://localhost:8000", "http://127.0.0.1:8000", "http://0.0.0.0:8000"], description="允许的跨域源")
    cors_allow_credentials: bool = Field(default=True, description="允许携带凭证")
    cors_allow_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="允许的HTTP方法")
    cors_allow_headers: List[str] = Field(default=["*"], description="允许的HTTP头")
    
    # 信任主机配置
    trusted_hosts: List[str] = Field(default=["*"], description="信任的主机列表")
    
    # API配置
    api_v1_prefix: str = Field(default="/api/v1", description="API v1前缀")
    docs_url: str = Field(default="/docs", description="API文档URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc文档URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI JSON URL")
    
    # 分页配置
    default_page_size: int = Field(default=100, description="默认分页大小")
    max_page_size: int = Field(default=500, description="最大分页大小")
    
    # 数据保留策略
    data_retention_days: int = Field(default=90, description="数据保留天数")
    log_retention_days: int = Field(default=30, description="日志保留天数")
    
    # 监控配置
    alert_threshold_percentage: float = Field(default=5.0, description="告警阈值百分比")
    alert_check_interval_minutes: int = Field(default=5, description="告警检查间隔(分钟)")
    
    # 去重配置
    dedup_enabled: bool = Field(default=True, description="是否启用数据去重")
    dedup_window_minutes: int = Field(default=1, description="去重时间窗口(分钟)")
    
    # 性能配置
    batch_size: int = Field(default=1000, description="批处理大小")
    query_timeout_seconds: int = Field(default=30, description="查询超时时间(秒)")
    
    # 安全配置
    secret_key: str = Field(default="your-secret-key-here", description="应用密钥")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # 忽略额外的环境变量
    }
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return self.database_url
    
    def get_redis_url(self) -> Optional[str]:
        """获取Redis连接URL"""
        if self.redis_url:
            if self.redis_password:
                # 如果有密码，构建带密码的URL
                return f"redis://:{self.redis_password}@{self.redis_url.replace('redis://', '')}/{self.redis_db}"
            return f"{self.redis_url}/{self.redis_db}"
        return None
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment.lower() == "development"
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment.lower() == "production"
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置（单例模式）"""
    return Settings()