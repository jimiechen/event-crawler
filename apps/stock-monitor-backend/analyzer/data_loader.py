"""
数据加载模块
负责读取和解析澳客网格式的足彩数据JSON文件
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class HandicapType(Enum):
    """盘口类型枚举"""
    QUARTER_GOAL = "半球/一球"  # 0.75
    HALF_GOAL = "半球"  # 0.5
    ONE_GOAL = "一球"  # 1.0
    ONE_QUARTER = "一球/球半"  # 1.25
    ONE_HALF = "球半"  # 1.5
    ONE_QUARTER_TWO = "球半/两球"  # 1.75
    TWO_GOAL = "两球"  # 2.0
    TWO_QUARTER = "两球/两半"  # 2.25
    TWO_HALF = "两半"  # 2.5
    UNKNOWN = "未知"


class OddsType(Enum):
    """赔率类型枚举"""
    HOME_WIN = "胜"
    DRAW = "平"
    AWAY_WIN = "负"


@dataclass
class MatchInfo:
    """比赛基本信息"""
    match_id: str
    home_team: str
    away_team: str
    score_text: str
    league: str


@dataclass
class HistoricalMatch:
    """历史比赛记录"""
    match_id: str
    league: str
    date: str
    score: str
    result: str
    opponent: str
    opponent_rank: str


@dataclass
class FutureMatch:
    """未来比赛安排"""
    league: str
    date: str
    home_team: str
    away_team: str
    interval: str


@dataclass
class HandicapCompany:
    """单家公司亚盘数据"""
    company: str
    initial_home: float
    initial_away: float
    initial_pan: float
    latest_home: float
    latest_away: float
    latest_pan: float


@dataclass
class EuroOddsCompany:
    """单家公司欧赔数据"""
    company: str
    initial_win: float
    initial_draw: float
    initial_loss: float
    latest_win: float
    latest_draw: float
    latest_loss: float


@dataclass
class FiveFactor:
    """五大因子分析"""
    factor: str
    home_win: str
    draw: str
    home_loss: str
    suggestion: str


@dataclass
class BetExchangeData:
    """投注交易所数据"""
    result: str
    index: float
    save_amount: str
    profit: str
    hot_cold: int


class DataLoader:
    """数据加载器类"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.raw_data: Dict[str, Any] = {}
        self.match_info: Optional[MatchInfo] = None
        self.home_history: List[HistoricalMatch] = []
        self.away_history: List[HistoricalMatch] = []
        self.head_to_head: List[HistoricalMatch] = []
        self.home_future: List[FutureMatch] = []
        self.away_future: List[FutureMatch] = []
        self.handicap_companies: List[HandicapCompany] = []
        self.euro_companies: List[EuroOddsCompany] = []
        self.five_factors: List[FiveFactor] = []
        self.exchanges: Dict[str, Any] = {}
        self.form_analysis: Dict[str, Any] = {}
        self.game_points: Dict[str, Any] = {}
        self.game_points_recent: Dict[str, Any] = {}
    
    def load(self) -> bool:
        """加载JSON数据文件"""
        if not self.data_path.exists():
            print(f"错误: 数据文件不存在 - {self.data_path}")
            return False
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            
            self._parse_match_info()
            self._parse_histories()
            self._parse_future_matches()
            self._parse_handicap()
            self._parse_euro_odds()
            self._parse_five_factors()
            self._parse_exchanges()
            self._parse_form_analysis()
            self._parse_game_points()
            
            return True
        except Exception as e:
            print(f"错误: 加载数据失败 - {e}")
            return False
    
    def _parse_match_info(self):
        """解析比赛基本信息"""
        info = self.raw_data.get('match_info', {})
        self.match_info = MatchInfo(
            match_id=self.raw_data.get('match_id', ''),
            home_team=info.get('home_team', ''),
            away_team=info.get('away_team', ''),
            score_text=info.get('score_text', ''),
            league=info.get('league', '')
        )
    
    def _parse_histories(self):
        """解析历史战绩"""
        for match in self.raw_data.get('home_history', []):
            self.home_history.append(HistoricalMatch(
                match_id=match.get('match_id', ''),
                league=match.get('league', ''),
                date=match.get('date', ''),
                score=match.get('score', ''),
                result=match.get('result', ''),
                opponent=match.get('opponent', ''),
                opponent_rank=match.get('opponent_rank', '')
            ))
        
        for match in self.raw_data.get('away_history', []):
            self.away_history.append(HistoricalMatch(
                match_id=match.get('match_id', ''),
                league=match.get('league', ''),
                date=match.get('date', ''),
                score=match.get('score', ''),
                result=match.get('result', ''),
                opponent=match.get('opponent', ''),
                opponent_rank=match.get('opponent_rank', '')
            ))
        
        for match in self.raw_data.get('head_to_head', []):
            self.head_to_head.append(HistoricalMatch(
                match_id=match.get('match_id', ''),
                league=match.get('league', ''),
                date=match.get('date', ''),
                score=match.get('score', ''),
                result=match.get('result', ''),
                opponent=match.get('opponent', ''),
                opponent_rank=match.get('opponent_rank', '')
            ))
    
    def _parse_future_matches(self):
        """解析未来比赛"""
        future_data = self.raw_data.get('future_matches', {})
        for match in future_data.get('home', []):
            self.home_future.append(FutureMatch(
                league=match.get('league', ''),
                date=match.get('date', ''),
                home_team=match.get('home_team', ''),
                away_team=match.get('away_team', ''),
                interval=match.get('interval', '')
            ))
        
        for match in future_data.get('away', []):
            self.away_future.append(FutureMatch(
                league=match.get('league', ''),
                date=match.get('date', ''),
                home_team=match.get('home_team', ''),
                away_team=match.get('away_team', ''),
                interval=match.get('interval', '')
            ))
    
    def _parse_handicap(self):
        """解析亚盘数据"""
        for company_data in self.raw_data.get('handicap', []):
            initial = company_data.get('initial', {})
            latest = company_data.get('latest', {})
            
            company = HandicapCompany(
                company=company_data.get('company', ''),
                initial_home=float(initial.get('home', 0)),
                initial_away=float(initial.get('away', 0)),
                initial_pan=self._parse_pan_value(initial.get('pan', '未知')),
                latest_home=float(latest.get('home', 0)),
                latest_away=float(latest.get('away', 0)),
                latest_pan=self._parse_pan_value(latest.get('pan', '未知'))
            )
            self.handicap_companies.append(company)
    
    def _parse_euro_odds(self):
        """解析欧赔数据"""
        for company_data in self.raw_data.get('euro_odds', []):
            initial = company_data.get('initial', {})
            latest = company_data.get('latest', {})
            
            company = EuroOddsCompany(
                company=company_data.get('company', ''),
                initial_win=float(initial.get('win', 0)),
                initial_draw=float(initial.get('draw', 0)),
                initial_loss=float(initial.get('loss', 0)),
                latest_win=float(latest.get('win', 0)),
                latest_draw=float(latest.get('draw', 0)),
                latest_loss=float(latest.get('loss', 0))
            )
            self.euro_companies.append(company)
    
    def _parse_five_factors(self):
        """解析五大因子分析"""
        five_factors_data = self.raw_data.get('exchanges', {}).get('five_factors', [])
        for factor_data in five_factors_data:
            self.five_factors.append(FiveFactor(
                factor=factor_data.get('factor', ''),
                home_win=factor_data.get('home_win', ''),
                draw=factor_data.get('draw', ''),
                home_loss=factor_data.get('home_loss', ''),
                suggestion=factor_data.get('suggestion', '')
            ))
    
    def _parse_exchanges(self):
        """解析交易所数据"""
        self.exchanges = self.raw_data.get('exchanges', {})
    
    def _parse_form_analysis(self):
        """解析状态分析"""
        self.form_analysis = self.raw_data.get('form_analysis', {})
    
    def _parse_game_points(self):
        """解析积分数据"""
        self.game_points = self.raw_data.get('game_points', {})
        self.game_points_recent = self.raw_data.get('game_points_recent', {})
    
    def _parse_pan_value(self, pan_str: str) -> float:
        """将盘口字符串转换为数值"""
        pan_mapping = {
            "半球/一球": 0.75,
            "半球": 0.5,
            "一球": 1.0,
            "一球/球半": 1.25,
            "球半": 1.5,
            "球半/两球": 1.75,
            "两球": 2.0,
            "两球/两半": 2.25,
            "两半": 2.5,
            "两球/两半": 2.25,
            "半/一": 0.75,
            "一球/球半": 1.25,
        }
        return pan_mapping.get(pan_str, 0.0)
    
    def get_company(self, company_name: str) -> Optional[HandicapCompany]:
        """获取指定公司的亚盘数据"""
        for company in self.handicap_companies:
            if company_name in company.company:
                return company
        return None
    
    def get_avg_handicap(self) -> HandicapCompany:
        """获取平均指数公司的盘口数据"""
        return self.get_company("平均指数") or self.handicap_companies[0] if self.handicap_companies else None
    
    def get_major_companies(self, count: int = 5) -> List[HandicapCompany]:
        """获取主要博彩公司的盘口数据"""
        key_companies = ["澳门", "bet365", "威廉希尔", "立博", "皇冠"]
        result = []
        
        for key in key_companies:
            company = self.get_company(key)
            if company:
                result.append(company)
        
        if len(result) < count:
            result.extend(self.handicap_companies[:count-len(result)])
        
        return result[:count]


if __name__ == "__main__":
    loader = DataLoader("/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/processed_samples/1314249.json")
    if loader.load():
        print(f"成功加载数据: {loader.match_info.home_team} vs {loader.match_info.away_team}")
        print(f"亚盘公司数量: {len(loader.handicap_companies)}")
        print(f"欧赔公司数量: {len(loader.euro_companies)}")
