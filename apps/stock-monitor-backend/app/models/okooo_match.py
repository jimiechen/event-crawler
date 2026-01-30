# -*- coding: utf-8 -*-
from sqlalchemy import String, Integer, JSON, BigInteger, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class OkoooMatch(Base):
    """
    Okooo比赛数据模型
    存储爬取到的比赛基本信息和历史战绩详情
    """
    __tablename__ = "okooo_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    match_no: Mapped[str] = mapped_column(String(20), comment="比赛序号", nullable=True)
    match_type: Mapped[str] = mapped_column(String(20), comment="比赛类型", nullable=True)
    match_id: Mapped[str] = mapped_column(String(10), comment="比赛ID", nullable=True)
    league_name: Mapped[str] = mapped_column(String(100), comment="联赛名称", nullable=True)
    home_team: Mapped[str] = mapped_column(String(100), comment="主队名称", nullable=False)
    away_team: Mapped[str] = mapped_column(String(100), comment="客队名称", nullable=False)
    
    rangqiu: Mapped[str] = mapped_column(String(10), comment="北单让球", nullable=True)
    mask: Mapped[str] = mapped_column(String(2), comment="类型集合，1竞彩2北单3十四场,4北单+竞彩，5北单+14场，6ALL", nullable=True)
    
    match_time_text: Mapped[str] = mapped_column(String(100), comment="比赛时间文本", nullable=True)
    match_date: Mapped[str] = mapped_column(String(20), comment="比赛日期", nullable=True)
    
    handicap_data: Mapped[str] = mapped_column(Text, comment="亚盘数据", nullable=True)
    game_data: Mapped[str] = mapped_column(Text, comment="联赛数据", nullable=True)
    form_data: Mapped[str] = mapped_column(Text, comment="近期战绩", nullable=True)
    exchanges_data: Mapped[str] = mapped_column(Text, comment="盈亏数据", nullable=True)
    odds_data: Mapped[str] = mapped_column(Text, comment="欧赔数据", nullable=True)
    history_data: Mapped[str] = mapped_column(Text, comment="历史交锋完整数据", nullable=False)
    
    data: Mapped[dict] = mapped_column(JSON, comment="分析结果", nullable=True)
    analysis: Mapped[dict] = mapped_column(JSON, comment="爬虫数据聚合", nullable=True)
    
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self) -> str:
        return f"<OkoooMatch(id={self.id}, {self.home_team} vs {self.away_team})>"
