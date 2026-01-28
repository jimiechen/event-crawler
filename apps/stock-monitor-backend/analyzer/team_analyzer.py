"""
球队实力分析模块
基于多维度数据计算球队实力指数
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import re


@dataclass
class TeamStrength:
    """球队实力综合评估"""
    team_name: str
    overall_score: float = 0.0
    attack_score: float = 0.0
    defense_score: float = 0.0
    home_score: float = 0.0
    away_score: float = 0.0
    recent_form_score: float = 0.0
    head_to_head_score: float = 0.0
    valuation_score: float = 0.0
    league_position_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'team_name': self.team_name,
            'overall_score': self.overall_score,
            'attack_score': self.attack_score,
            'defense_score': self.defense_score,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'recent_form_score': self.recent_form_score,
            'head_to_head_score': self.head_to_head_score,
            'valuation_score': self.valuation_score,
            'league_position_score': self.league_position_score,
        }


@dataclass
class StrengthComparison:
    """两队实力对比结果"""
    home_team: str
    away_team: str
    strength_diff: float
    home_advantage: float
    expected_handicap: float
    actual_handicap: float
    shallow_risk: float
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'home_team': self.home_team,
            'away_team': self.away_team,
            'strength_diff': self.strength_diff,
            'home_advantage': self.home_advantage,
            'expected_handicap': self.expected_handicap,
            'actual_handicap': self.actual_handicap,
            'shallow_risk': self.shallow_risk,
            'analysis_details': self.analysis_details,
        }


class TeamAnalyzer:
    """球队实力分析器"""
    
    def __init__(self, home_history: List[Dict], away_history: List[Dict], 
                 head_to_head: List[Dict], form_analysis: Dict,
                 game_points: Dict, game_points_recent: Dict):
        self.home_history = home_history
        self.away_history = away_history
        self.head_to_head = head_to_head
        self.form_analysis = form_analysis
        self.game_points = game_points
        self.game_points_recent = game_points_recent
    
    def analyze_home_team(self, team_name: str) -> TeamStrength:
        """分析主队实力"""
        strength = TeamStrength(team_name=team_name)
        
        strength.valuation_score = self._analyze_valuation(self.form_analysis)
        strength.attack_score, strength.defense_score = self._analyze_technical_stats()
        strength.home_score = self._analyze_home_performance()
        strength.away_score = self._analyze_away_performance()
        strength.recent_form_score = self._analyze_recent_form()
        strength.head_to_head_score = self._analyze_h2h_advantage(team_name)
        strength.league_position_score = self._analyze_league_position()
        
        strength.overall_score = self._calculate_overall_score(strength)
        
        return strength
    
    def analyze_away_team(self, team_name: str) -> TeamStrength:
        """分析客队实力"""
        strength = TeamStrength(team_name=team_name)
        
        strength.valuation_score = self._analyze_away_valuation(self.form_analysis)
        strength.attack_score, strength.defense_score = self._analyze_away_technical_stats()
        strength.home_score = self._analyze_home_performance()
        strength.away_score = self._analyze_away_performance()
        strength.recent_form_score = self._analyze_away_recent_form()
        strength.head_to_head_score = self._analyze_h2h_disadvantage(team_name)
        strength.league_position_score = self._analyze_away_position()
        
        strength.overall_score = self._calculate_overall_score(strength)
        
        return strength
    
    def compare_teams(self, home_team: str, away_team: str) -> StrengthComparison:
        """对比两队实力"""
        home_strength = self.analyze_home_team(home_team)
        away_strength = self.analyze_away_team(away_team)
        
        strength_diff = home_strength.overall_score - away_strength.overall_score
        home_advantage = self._calculate_home_advantage(home_strength, away_strength)
        expected_handicap = self._calculate_expected_handicap(home_strength, away_strength)
        
        return StrengthComparison(
            home_team=home_team,
            away_team=away_team,
            strength_diff=strength_diff,
            home_advantage=home_advantage,
            expected_handicap=expected_handicap,
            actual_handicap=0.0,
            shallow_risk=0.0,
            analysis_details={
                'home_strength': home_strength.to_dict(),
                'away_strength': away_strength.to_dict(),
                'strength_diff_breakdown': self._get_diff_breakdown(home_strength, away_strength),
            }
        )
    
    def _parse_value(self, value_str: str) -> float:
        """解析球队身价字符串为数值（单位：万欧元）"""
        if not value_str or value_str == '-':
            return 0.0
        
        try:
            if '亿' in value_str:
                match = re.search(r'([\d.]+)', value_str)
                if match:
                    return float(match.group(1)) * 10000
            elif '万' in value_str:
                match = re.search(r'([\d.]+)', value_str)
                if match:
                    return float(match.group(1))
            else:
                match = re.search(r'([\d.]+)', value_str)
                if match:
                    return float(match.group(1)) / 10
        except:
            pass
        return 0.0
    
    def _analyze_valuation(self, form_analysis: Dict) -> float:
        """分析主队身价评分"""
        overview = form_analysis.get('overview', {})
        total_value = overview.get('total_value', '')
        
        if not total_value:
            return 50.0
        
        parts = total_value.split(',')
        for part in parts:
            if 'home' in part:
                return self._parse_value(part.split(':')[-1].strip()) / 1000
        
        return 50.0
    
    def _analyze_away_valuation(self, form_analysis: Dict) -> float:
        """分析客队身价评分"""
        overview = form_analysis.get('overview', {})
        total_value = overview.get('total_value', '')
        
        if not total_value:
            return 30.0
        
        parts = total_value.split(',')
        for part in parts:
            if 'away' in part:
                return self._parse_value(part.split(':')[-1].strip()) / 1000
        
        return 30.0
    
    def _analyze_technical_stats(self) -> tuple:
        """分析技术统计数据"""
        tech_comparison = self.form_analysis.get('technical_comparison', [])
        
        home_attack = 50.0
        home_defense = 50.0
        
        for stat in tech_comparison:
            label = stat.get('label', '')
            home_all = stat.get('home_all', '')
            away_all = stat.get('away_all', '')
            
            try:
                home_val = float(home_all.split()[0]) if home_all else 0
                away_val = float(away_all.split()[0]) if away_all else 0
                
                if '射门' in label:
                    home_attack = min(100, home_attack + home_val * 3)
                    home_defense = min(100, home_defense + away_val * 2)
                elif '进球' in label:
                    home_attack = min(100, home_attack + home_val * 10)
                elif '失球' in label:
                    home_defense = max(0, 80 - home_val * 10)
                elif '控球率' in label:
                    home_attack = min(100, home_attack + float(home_all.strip('%')) / 2)
            except:
                continue
        
        return home_attack, home_defense
    
    def _analyze_away_technical_stats(self) -> tuple:
        """分析客队技术统计数据"""
        tech_comparison = self.form_analysis.get('technical_comparison', [])
        
        away_attack = 50.0
        away_defense = 50.0
        
        for stat in tech_comparison:
            label = stat.get('label', '')
            home_all = stat.get('home_all', '')
            away_all = stat.get('away_all', '')
            
            try:
                home_val = float(home_all.split()[0]) if home_all else 0
                away_val = float(away_all.split()[0]) if away_all else 0
                
                if '射门' in label:
                    away_attack = min(100, away_attack + away_val * 3)
                    away_defense = min(100, away_defense + home_val * 2)
                elif '进球' in label:
                    away_attack = min(100, away_attack + away_val * 10)
                elif '失球' in label:
                    away_defense = max(0, 80 - away_val * 10)
                elif '控球率' in label:
                    away_attack = min(100, away_attack + float(away_all.strip('%')) / 2)
            except:
                continue
        
        return away_attack, away_defense
    
    def _analyze_home_performance(self) -> float:
        """分析主队主场表现"""
        if not self.home_history:
            return 50.0
        
        wins = sum(1 for m in self.home_history if m.result == '赢')
        total = len(self.home_history)
        
        if total == 0:
            return 50.0
        
        win_rate = wins / total
        recent_wins = sum(1 for m in self.home_history[:5] if m.result == '赢')
        
        score = win_rate * 60 + (recent_wins / 5) * 40
        return min(100, score)
    
    def _analyze_away_performance(self) -> float:
        """分析主队客场比赛表现（用于评估客队）"""
        if not self.home_history:
            return 40.0
        
        losses = sum(1 for m in self.home_history if m.result == '输')
        total = len(self.home_history)
        
        if total == 0:
            return 40.0
        
        loss_rate = losses / total
        score = 60 - loss_rate * 40
        return max(0, min(100, score))
    
    def _analyze_recent_form(self) -> float:
        """分析主队近期状态"""
        recent_matches = self.home_history[:6]
        
        if not recent_matches:
            return 50.0
        
        win_points = sum(3 for m in recent_matches if m.result == '赢')
        draw_points = sum(1 for m in recent_matches if m.result == '走')
        total_points = len(recent_matches) * 3
        
        if total_points == 0:
            return 50.0
        
        return min(100, (win_points + draw_points) / total_points * 100)
    
    def _analyze_away_recent_form(self) -> float:
        """分析客队近期状态"""
        recent_matches = self.away_history[:6]
        
        if not recent_matches:
            return 45.0
        
        win_points = sum(3 for m in recent_matches if m.result == '赢')
        draw_points = sum(1 for m in recent_matches if m.result == '走')
        total_points = len(recent_matches) * 3
        
        if total_points == 0:
            return 45.0
        
        return min(100, (win_points + draw_points) / total_points * 100)
    
    def _analyze_h2h_advantage(self, team_name: str) -> float:
        """分析主队对客队的历史交锋优势"""
        h2h_matches = [m for m in self.head_to_head if team_name in m.opponent]
        
        if not h2h_matches:
            return 50.0
        
        wins = sum(1 for m in h2h_matches if m.result == '赢')
        total = len(h2h_matches)
        
        if total == 0:
            return 50.0
        
        return min(100, wins / total * 100 + 20)
    
    def _analyze_h2h_disadvantage(self, team_name: str) -> float:
        """分析客队对主队的历史交锋劣势"""
        h2h_matches = [m for m in self.head_to_head if team_name in m.opponent]
        
        if not h2h_matches:
            return 45.0
        
        losses = sum(1 for m in h2h_matches if m.result == '输')
        total = len(h2h_matches)
        
        if total == 0:
            return 45.0
        
        return max(0, 50 - losses / total * 30)
    
    def _analyze_league_position(self) -> float:
        """分析联赛排名评分"""
        points_table = self.game_points
        if isinstance(self.game_points, dict):
            points_table = self.game_points.get('points_table', [])
        elif not isinstance(self.game_points, list):
            points_table = []
        
        for team in points_table:
            if isinstance(team, dict) and '利雅得胜利' in team.get('team', ''):
                rank = int(team.get('rank', 10))
                points = int(team.get('points', 0))
                
                rank_score = max(0, 100 - rank * 5)
                points_score = min(100, points / 40 * 100)
                
                return (rank_score + points_score) / 2
        
        return 50.0
    
    def _analyze_away_position(self) -> float:
        """分析客队联赛排名评分"""
        points_table = self.game_points
        if isinstance(self.game_points, dict):
            points_table = self.game_points.get('points_table', [])
        elif not isinstance(self.game_points, list):
            points_table = []
        
        for team in points_table:
            if isinstance(team, dict) and '布赖合作' in team.get('team', ''):
                rank = int(team.get('rank', 10))
                points = int(team.get('points', 0))
                
                rank_score = max(0, 100 - rank * 5)
                points_score = min(100, points / 40 * 100)
                
                return (rank_score + points_score) / 2
        
        return 45.0
    
    def _calculate_overall_score(self, strength: TeamStrength) -> float:
        """计算综合实力分数"""
        weights = {
            'valuation': 0.25,
            'attack': 0.20,
            'defense': 0.15,
            'home': 0.15,
            'recent_form': 0.15,
            'h2h': 0.10,
        }
        
        score = (
            strength.valuation_score * weights['valuation'] +
            strength.attack_score * weights['attack'] +
            strength.defense_score * weights['defense'] +
            strength.home_score * weights['home'] +
            strength.recent_form_score * weights['recent_form'] +
            strength.head_to_head_score * weights['h2h']
        )
        
        return min(100, max(0, score))
    
    def _calculate_home_advantage(self, home: TeamStrength, away: TeamStrength) -> float:
        """计算主场优势"""
        home_field_advantage = home.home_score - home.away_score
        opponent_weakness = 50 - away.away_score
        
        return min(30, (home_field_advantage + opponent_weakness) / 2)
    
    def _calculate_expected_handicap(self, home: TeamStrength, away: TeamStrength) -> float:
        """计算合理的预期盘口"""
        strength_diff = home.overall_score - away.overall_score
        
        if strength_diff >= 50:
            return 2.0
        elif strength_diff >= 35:
            return 1.75
        elif strength_diff >= 25:
            return 1.5
        elif strength_diff >= 15:
            return 1.25
        elif strength_diff >= 5:
            return 1.0
        elif strength_diff >= -5:
            return 0.75
        elif strength_diff >= -15:
            return 0.5
        else:
            return 0.25
    
    def _get_diff_breakdown(self, home: TeamStrength, away: TeamStrength) -> Dict[str, float]:
        """获取实力差距详细分解"""
        return {
            'valuation_diff': home.valuation_score - away.valuation_score,
            'attack_diff': home.attack_score - away.attack_score,
            'defense_diff': home.defense_score - away.defense_score,
            'form_diff': home.recent_form_score - away.recent_form_score,
            'h2h_diff': home.head_to_head_score - away.head_to_head_score,
        }


def calculate_team_strength(data_loader) -> tuple:
    """便捷函数：计算两队实力"""
    analyzer = TeamAnalyzer(
        home_history=data_loader.home_history,
        away_history=data_loader.away_history,
        head_to_head=data_loader.head_to_head,
        form_analysis=data_loader.form_analysis,
        game_points=data_loader.game_points,
        game_points_recent=data_loader.game_points_recent
    )
    
    home_strength = analyzer.analyze_home_team(data_loader.match_info.home_team)
    away_strength = analyzer.analyze_away_team(data_loader.match_info.away_team)
    comparison = analyzer.compare_teams(
        data_loader.match_info.home_team,
        data_loader.match_info.away_team
    )
    
    return home_strength, away_strength, comparison


if __name__ == "__main__":
    from data_loader import DataLoader
    
    loader = DataLoader("/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/processed_samples/1314249.json")
    if loader.load():
        home, away, comparison = calculate_team_strength(loader)
        
        print(f"\n主队({loader.match_info.home_team})实力分析:")
        for k, v in home.to_dict().items():
            print(f"  {k}: {v:.2f}")
        
        print(f"\n客队({loader.match_info.away_team})实力分析:")
        for k, v in away.to_dict().items():
            print(f"  {k}: {v:.2f}")
        
        print(f"\n实力对比:")
        print(f"  实力差距: {comparison.strength_diff:.2f}")
        print(f"  主场优势: {comparison.home_advantage:.2f}")
        print(f"  预期盘口: {comparison.expected_handicap:.2f}")
