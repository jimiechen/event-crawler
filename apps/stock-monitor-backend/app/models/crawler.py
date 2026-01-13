from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class CrawlerTarget(BaseModel):
    """爬虫目标URL配置表"""
    __tablename__ = "crawler_targets"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, comment="平台(bilibili, weibo, etc)")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="目标名称")
    url: Mapped[str] = mapped_column(Text, nullable=False, comment="目标URL或关键词")
    target_type: Mapped[str] = mapped_column(String(20), default="url", comment="类型: url, keyword")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    xpath_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="XPath配置(JSON)")
    
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="上次爬取时间")
    last_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="上次状态")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    class Config:
        from_attributes = True

class CrawlerResult(BaseModel):
    """爬虫结果表"""
    __tablename__ = "crawler_results"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, comment="平台")
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="关联的目标ID")
    
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="内容/标题")
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="作者")
    publish_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="发布时间")
    
    likes: Mapped[int] = mapped_column(Integer, default=0, comment="点赞数")
    comments: Mapped[int] = mapped_column(Integer, default=0, comment="评论数")
    shares: Mapped[int] = mapped_column(Integer, default=0, comment="分享数")
    
    url: Mapped[str] = mapped_column(Text, nullable=False, comment="原文链接")
    data_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="原始数据ID")
    
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="爬取时间")
    
    class Config:
        from_attributes = True

class CrawlerLoginStatus(BaseModel):
    """爬虫登录状态表"""
    __tablename__ = "crawler_login_status"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, comment="平台")
    is_logged_in: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已登录")
    message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="状态消息")
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="检查时间")
