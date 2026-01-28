# -*- coding: utf-8 -*-

from enum import Enum
from typing import Optional

class OkoooPageType(Enum):
    """
    Okooo页面类型枚举
    """
    MATCH_DETAIL = "match_detail"  # 比赛详情页（包含概览、阵容等）
    HISTORY = "history"            # 历史战绩页
    MOBILE_HISTORY = "mobile_history" # 手机版历史战绩页
    MOBILE_ODDS = "mobile_odds"       # 手机版欧指页
    MOBILE_HANDICAP = "mobile_handicap" # 手机版亚指页
    MOBILE_EXCHANGES = "mobile_exchanges" # 手机版盈亏页
    MOBILE_FORM = "mobile_form"       # 手机版阵容页
    MOBILE_GAME = "mobile_game"       # 手机版积分页
    MOBILE_CHANGE = "mobile_change"   # 手机版指数变化页
    EXCHANGES = "exchanges"        # 欧赔页面（百家欧赔）
    AH = "ah"                      # 亚盘页面（亚盘对比）
    ANALYSIS = "analysis"          # 数据分析页

class OkoooUrlBuilder:
    """
    Okooo URL构造器
    负责生成各类Okooo页面的URL
    """
    
    BASE_URL = "https://m.okooo.com"
    
    @classmethod
    def build_match_url(cls, match_id: str, page_type: OkoooPageType = OkoooPageType.MATCH_DETAIL) -> str:
        """
        构建比赛相关页面的URL
        
        Args:
            match_id: 比赛ID
            page_type: 页面类型
            
        Returns:
            str: 完整的URL
        """
        if not match_id:
            raise ValueError("match_id cannot be empty")
            
        base_match_url = f"{cls.BASE_URL}/soccer/match/{match_id}"
        
        if page_type == OkoooPageType.MATCH_DETAIL:
            return f"{base_match_url}/"
        elif page_type == OkoooPageType.HISTORY:
            return f"{base_match_url}/history/"
        elif page_type == OkoooPageType.MOBILE_HISTORY:
            return f"https://m.okooo.com/match/history.php?MatchID={match_id}"
        elif page_type == OkoooPageType.MOBILE_ODDS:
            return f"https://m.okooo.com/match/odds.php?MatchID={match_id}&from="
        elif page_type == OkoooPageType.MOBILE_HANDICAP:
            return f"https://m.okooo.com/match/handicap.php?MatchID={match_id}&from="
        elif page_type == OkoooPageType.EXCHANGES:
            return f"{base_match_url}/exchanges/"
        elif page_type == OkoooPageType.AH:
            return f"{base_match_url}/ah/"
        elif page_type == OkoooPageType.ANALYSIS:
            return f"{base_match_url}/analysis/"
        else:
            return f"{base_match_url}/"

    @classmethod
    def get_match_id_from_url(cls, url: str) -> Optional[str]:
        """
        从URL中提取比赛ID
        
        Args:
            url: 完整URL
            
        Returns:
            Optional[str]: 比赛ID或None
        """
        if not url:
            return None
            
        import re
        # 匹配 /soccer/match/123456/ 或 /soccer/match/123456/history/ 等
        pattern = r"/soccer/match/(\d+)"
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
