# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class OkoooMatch(Base, TimestampMixin):
    """
    Okooo比赛数据模型
    存储爬取到的比赛基本信息和历史战绩详情
    """
    __tablename__ = "okooo_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    league_name: Mapped[Optional[str]] = mapped_column(String(100), comment="联赛名称", nullable=True)
    home_team: Mapped[str] = mapped_column(String(100), comment="主队名称", index=True)
    away_team: Mapped[str] = mapped_column(String(100), comment="客队名称", index=True)
    match_time_text: Mapped[Optional[str]] = mapped_column(String(100), comment="比赛时间文本", nullable=True)
    
    # 存储完整解析数据，包含 match_info, home_history, away_history, head_to_head, future_matches
    history_data: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="历史交锋完整数据")

    def __repr__(self) -> str:
        return f"<OkoooMatch(id={self.id}, {self.home_team} vs {self.away_team})>"
