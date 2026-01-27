"""
诱导盘检测模块
检测博彩公司是否通过异常盘口水位诱导玩家投注
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TrapType(Enum):
    """诱导盘类型枚举"""
    NO_TRAP = "无诱导"
    WATER_TRAP = "水位诱导"
    HANDICAP_TRAP = "盘口诱导"
    ASIA_EURO_TRAP = "亚欧矛盾"
    COMPANY_TRAP = "公司分歧"
    LATE_TRAP = "临场诱盘"


@dataclass
class TrapAnalysisResult:
    """诱导盘分析结果"""
    is_trap: bool
    trap_type: TrapType
    trap_score: float
    trap_indicators: Dict[str, Any]
    reasons: List[str]
    warnings: List[str]
    target_direction: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_trap': self.is_trap,
            'trap_type': self.trap_type.value,
            'trap_score': self.trap_score,
            'trap_indicators': self.trap_indicators,
            'reasons': self.reasons,
            'warnings': self.warnings,
            'target_direction': self.target_direction,
            'confidence': self.confidence,
        }


@dataclass
class CompanyTrapResult:
    """单家公司诱导盘分析结果"""
    company: str
    is_suspicious: bool
    trap_type: TrapType
    water_change: float
    pan_change: float
    suspicion_score: float
    details: str


class TrapDetector:
    """诱导盘检测器"""
    
    def __init__(self, handicap_companies: List, euro_companies: List, 
                 exchanges: Dict[str, Any], team_comparison: Dict[str, Any]):
        self.handicap_companies = handicap_companies
        self.euro_companies = euro_companies
        self.exchanges = exchanges
        self.team_comparison = team_comparison
        self.strength_diff = team_comparison.get('strength_diff', 30.0)
    
    def analyze(self) -> TrapAnalysisResult:
        """执行诱导盘分析"""
        water_trap_result = self._analyze_water_trap()
        handicap_trap_result = self._analyze_handicap_trap()
        asia_euro_result = self._analyze_asia_euro_consistency()
        company_trap_result = self._analyze_company_divergence()
        late_trap_result = self._analyze_late_trap()
        
        all_results = [
            water_trap_result,
            handicap_trap_result,
            asia_euro_result,
            company_trap_result,
            late_trap_result
        ]
        
        trap_scores = [r[1] for r in all_results if r[1] > 0]
        max_trap_score = max(trap_scores) if trap_scores else 0
        
        primary_trap = max(all_results, key=lambda x: x[1])
        
        reasons = []
        warnings = []
        
        for trap_type, score, detail_reasons, detail_warnings in all_results:
            if score > 40:
                reasons.extend(detail_reasons)
            if score > 30:
                warnings.extend(detail_warnings)
        
        if max_trap_score > 50:
            trap_type = primary_trap[0]
        else:
            trap_type = TrapType.NO_TRAP
        
        target_direction = self._determine_trap_direction(primary_trap, max_trap_score)
        confidence = self._calculate_confidence()
        
        trap_indicators = {
            'water_trap_score': water_trap_result[1],
            'handicap_trap_score': handicap_trap_result[1],
            'asia_euro_score': asia_euro_result[1],
            'company_trap_score': company_trap_result[1],
            'late_trap_score': late_trap_result[1],
        }
        
        return TrapAnalysisResult(
            is_trap=max_trap_score > 40,
            trap_type=trap_type,
            trap_score=max_trap_score,
            trap_indicators=trap_indicators,
            reasons=reasons[:5],
            warnings=warnings[:5],
            target_direction=target_direction,
            confidence=confidence
        )
    
    def _analyze_water_trap(self) -> Tuple[TrapType, float, List[str], List[str]]:
        """分析水位诱导"""
        reasons = []
        warnings = []
        score = 0.0
        
        for company in self.handicap_companies:
            company_name = company.company
            
            if not any(c in company_name for c in ['澳门', 'bet365', '立博', '威廉希尔', '平均指数']):
                continue
            
            water_change = company.initial_home - company.latest_home
            pan_changed = company.latest_pan != company.initial_pan
            
            if water_change > 0.15 and not pan_changed:
                score = max(score, 60)
                reasons.append(f"{company_name}主胜水位大幅下降{water_change:.2f}但盘口未跟随调整")
            elif water_change > 0.10 and not pan_changed:
                score = max(score, 45)
                warnings.append(f"{company_name}存在水位异常变动，可能为诱导信号")
            
            if company.latest_home < 1.65 and company.latest_pan <= 1.5:
                score = max(score, 50)
                reasons.append(f"{company_name}主胜水位过低({company.latest_home})配合浅盘，可能诱买主队")
            
            if abs(company.latest_home - company.latest_away) > 0.4:
                score = max(score, 30)
                warnings.append(f"{company_name}水位失衡，可能存在异常")
        
        trap_type = TrapType.WATER_TRAP if score > 40 else TrapType.NO_TRAP
        return trap_type, score, reasons, warnings
    
    def _analyze_handicap_trap(self) -> Tuple[TrapType, float, List[str], List[str]]:
        """分析盘口诱导"""
        reasons = []
        warnings = []
        score = 0.0
        
        avg_initial = sum(c.initial_pan for c in self.handicap_companies) / len(self.handicap_companies)
        avg_latest = sum(c.latest_pan for c in self.handicap_companies) / len(self.handicap_companies)
        
        pan_movement = avg_latest - avg_initial
        
        if pan_movement > 0.25:
            for company in self.handicap_companies:
                if company.latest_pan - company.initial_pan > 0.5:
                    score = max(score, 55)
                    reasons.append(f"{company_name}大幅升盘{company.latest_pan - company.initial_pan:.2f}球，需警惕诱盘")
        
        if pan_movement < -0.25:
            for company in self.handicap_companies:
                if company.initial_pan - company.latest_pan > 0.25:
                    score = max(score, 45)
                    warnings.append(f"{company_name}降盘幅度异常，可能对主队信心不足")
        
        home_waters = [c.latest_home for c in self.handicap_companies if c.latest_home > 0]
        away_waters = [c.latest_away for c in self.handicap_companies if c.latest_away > 0]
        
        if home_waters and away_waters:
            avg_home = sum(home_waters) / len(home_waters)
            avg_away = sum(away_waters) / len(away_waters)
            
            if avg_home < 1.70 and avg_latest <= 1.5:
                score = max(score, 40)
                warnings.append("主胜低水位配合浅盘，存在诱导主队投注嫌疑")
        
        trap_type = TrapType.HANDICAP_TRAP if score > 40 else TrapType.NO_TRAP
        return trap_type, score, reasons, warnings
    
    def _analyze_asia_euro_consistency(self) -> Tuple[TrapType, float, List[str], List[str]]:
        """分析亚欧赔一致性"""
        reasons = []
        warnings = []
        score = 0.0
        
        euro_win_changes = []
        asian_home_changes = []
        
        major_euro = ['威廉希尔', '立博', 'bet365', '澳门彩票', '99家平均']
        major_asian = ['澳门', 'bet365', '立博', '皇冠', '平均指数']
        
        euro_dict = {c.company: c for c in self.euro_companies}
        asian_dict = {c.company: c for c in self.handicap_companies}
        
        for company_name in major_euro:
            if company_name in euro_dict:
                euro = euro_dict[company_name]
                euro_win_changes.append(euro.initial_win - euro.latest_win)
        
        for company_name in major_asian:
            if company_name in asian_dict:
                asian = asian_dict[company_name]
                asian_home_changes.append(asian.initial_home - asian.latest_home)
        
        if euro_win_changes and asian_home_changes:
            avg_euro_change = sum(euro_win_changes) / len(euro_win_changes)
            avg_asian_change = sum(asian_home_changes) / len(asian_home_changes)
            
            if avg_euro_change > 0.05 and avg_asian_change < 0:
                score = max(score, 70)
                reasons.append("欧赔胜赔上升而亚盘主胜降水严重，亚欧走势矛盾")
                reasons.append("这是典型的诱导盘特征，庄家可能在诱买主队")
            elif avg_euro_change < -0.05 and avg_asian_change > 0.1:
                score = max(score, 60)
                reasons.append("欧赔胜赔大降但亚盘主胜升水，存在诱客可能")
            
            if abs(avg_euro_change - avg_asian_change) > 0.15:
                score = max(score, 45)
                warnings.append(f"亚欧走势分歧度达{abs(avg_euro_change - avg_asian_change):.2f}，需谨慎判断")
        
        trap_type = TrapType.ASIA_EURO_TRAP if score > 40 else TrapType.NO_TRAP
        return trap_type, score, reasons, warnings
    
    def _analyze_company_divergence(self) -> Tuple[TrapType, float, List[str], List[str]]:
        """分析公司分歧"""
        reasons = []
        warnings = []
        score = 0.0
        
        company_pans = []
        company_home_waters = []
        
        for company in self.handicap_companies:
            if company.latest_pan > 0:
                company_pans.append((company.company, company.latest_pan))
                company_home_waters.append((company.company, company.latest_home))
        
        if len(company_pans) < 3:
            return TrapType.NO_TRAP, 0.0, [], []
        
        pans = [p[1] for p in company_pans]
        avg_pan = sum(pans) / len(pans)
        pan_variance = sum((p - avg_pan) ** 2 for p in pans) / len(pans)
        pan_std = pan_variance ** 0.5
        
        if pan_std > 0.25:
            score = max(score, 55)
            reasons.append(f"各公司盘口分歧严重（标准差{pan_std:.2f}），可能存在异常")
        
        home_waters = [w[1] for w in company_home_waters]
        avg_home = sum(home_waters) / len(home_waters)
        water_variance = sum((w - avg_home) ** 2 for w in home_waters) / len(home_waters)
        water_std = water_variance ** 0.5
        
        if water_std > 0.15:
            score = max(score, 40)
            warnings.append(f"主胜水位分歧较大（标准差{water_std:.2f}），需关注")
        
        conservative = ['澳门', '香港马会']
        aggressive = ['bet365', '立博', '必发']
        
        conservative_pans = []
        aggressive_pans = []
        
        for company_name, pan in company_pans:
            if any(c in company_name for c in conservative):
                conservative_pans.append(pan)
            elif any(c in company_name for c in aggressive):
                aggressive_pans.append(pan)
        
        if conservative_pans and aggressive_pans:
            avg_conservative = sum(conservative_pans) / len(conservative_pans)
            avg_aggressive = sum(aggressive_pans) / len(aggressive_pans)
            
            if avg_conservative - avg_aggressive > 0.25:
                score = max(score, 50)
                reasons.append("保守公司与激进公司盘口差距过大，可能存在诱盘")
        
        trap_type = TrapType.COMPANY_TRAP if score > 40 else TrapType.NO_TRAP
        return trap_type, score, reasons, warnings
    
    def _analyze_late_trap(self) -> Tuple[TrapType, float, List[str], List[str]]:
        """分析临场诱盘"""
        reasons = []
        warnings = []
        score = 0.0
        
        five_factors = self.exchanges.get('five_factors', [])
        
        for factor in five_factors:
            factor_name = factor.get('factor', '')
            suggestion = factor.get('suggestion', '')
            
            if factor_name == '指数':
                if '主胜' in suggestion and len(suggestion.split(',')) > 1:
                    score = max(score, 45)
                    warnings.append("指数因子推荐主胜但有其他选项，可能存在分歧")
            
            if factor_name == '人气':
                if '主胜' in suggestion:
                    popularity_data = self.exchanges.get('jczq_popularity', [])
                    for pop in popularity_data:
                        if pop.get('result') == '胜':
                            hot_cold = int(pop.get('hot_cold', 0))
                            if hot_cold > 5:
                                score = max(score, 35)
                                warnings.append("主胜热度较高，需警惕过热风险")
        
        betfair = self.exchanges.get('betfair_transaction', [])
        for bet in betfair:
            if bet.get('result') == '胜':
                hot_cold = int(bet.get('hot_cold', 0))
                if hot_cold > 20:
                    score = max(score, 40)
                    warnings.append("必发主胜交易热度异常偏高，可能存在诱盘风险")
        
        trap_type = TrapType.LATE_TRAP if score > 40 else TrapType.NO_TRAP
        return trap_type, score, reasons, warnings
    
    def _determine_trap_direction(self, primary_trap: Tuple, score: float) -> str:
        """判断诱导方向"""
        if score < 30:
            return "无明确诱导方向"
        
        trap_type = primary_trap[0]
        
        if trap_type == TrapType.WATER_TRAP:
            for company in self.handicap_companies:
                if '澳门' in company.company:
                    if company.latest_home < 1.70:
                        return "诱导投注主胜"
                    elif company.latest_away > 2.0:
                        return "诱导投注客胜"
        
        if trap_type == TrapType.ASIA_EURO_TRAP:
            euro_dict = {c.company: c for c in self.euro_companies}
            for company_name in ['威廉希尔', '必发']:
                if company_name in euro_dict:
                    euro = euro_dict[company_name]
                    if euro.latest_win > euro.initial_win:
                        return "欧赔示弱，可能诱导投注下盘"
        
        return "需结合其他指标综合判断"
    
    def _calculate_confidence(self) -> float:
        """计算分析置信度"""
        base_confidence = 0.5
        
        if len(self.handicap_companies) >= 10:
            base_confidence += 0.15
        elif len(self.handicap_companies) >= 5:
            base_confidence += 0.10
        
        if len(self.euro_companies) >= 10:
            base_confidence += 0.15
        elif len(self.euro_companies) >= 5:
            base_confidence += 0.10
        
        if self.exchanges.get('five_factors'):
            base_confidence += 0.10
        
        return min(0.95, base_confidence)
    
    def get_trap_signals(self) -> Dict[str, Any]:
        """获取诱导盘关键信号"""
        return {
            'total_trap_score': self._calculate_total_trap_score(),
            'key_signals': self._identify_key_signals(),
            'risk_level': self._assess_risk_level(),
        }
    
    def _calculate_total_trap_score(self) -> float:
        """计算总体诱导评分"""
        scores = []
        
        for company in self.handicap_companies:
            water_change = abs(company.initial_home - company.latest_home)
            if water_change > 0.15 and company.latest_pan == company.initial_pan:
                scores.append(min(100, water_change * 300))
            
            if company.latest_home < 1.60 and company.latest_pan <= 1.5:
                scores.append(50)
        
        if not scores:
            return 0.0
        
        return min(100, sum(scores) / len(scores))
    
    def _identify_key_signals(self) -> List[str]:
        """识别关键诱导信号"""
        signals = []
        
        for company in self.handicap_companies:
            if '澳门' in company.company:
                water_change = company.initial_home - company.latest_home
                if water_change > 0.12:
                    signals.append(f"澳门主胜水位下降{water_change:.2f}但盘口未动")
                
                if company.latest_home < 1.65 and company.latest_pan <= 1.5:
                    signals.append("澳门主胜低水配浅盘，存在诱导嫌疑")
        
        euro_dict = {c.company: c for c in self.euro_companies}
        if '必发' in euro_dict:
            betfair = euro_dict['必发']
            if betfair.latest_win > 1.20 and betfair.initial_win < 1.10:
                signals.append("必发胜赔大幅上升，可能对主队信心不足")
        
        return signals[:5]
    
    def _assess_risk_level(self) -> str:
        """评估风险等级"""
        score = self._calculate_total_trap_score()
        
        if score >= 70:
            return "极高风险"
        elif score >= 50:
            return "高风险"
        elif score >= 30:
            return "中等风险"
        elif score >= 15:
            return "低风险"
        else:
            return "正常"


def analyze_trap_odds(data_loader, team_comparison: Dict[str, Any]) -> TrapAnalysisResult:
    """便捷函数：分析是否存在诱导盘"""
    detector = TrapDetector(
        handicap_companies=data_loader.handicap_companies,
        euro_companies=data_loader.euro_companies,
        exchanges=data_loader.exchanges,
        team_comparison=team_comparison
    )
    
    return detector.analyze()


if __name__ == "__main__":
    from data_loader import DataLoader
    from team_analyzer import calculate_team_strength
    
    loader = DataLoader("/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/processed_samples/1314249.json")
    if loader.load():
        _, _, comparison = calculate_team_strength(loader)
        
        print("\n=== 诱导盘分析 ===")
        detector = TrapDetector(
            handicap_companies=loader.handicap_companies,
            euro_companies=loader.euro_companies,
            exchanges=loader.exchanges,
            team_comparison=comparison.to_dict()
        )
        
        result = detector.analyze()
        print(f"诱导类型: {result.trap_type.value}")
        print(f"诱导评分: {result.trap_score:.1f}")
        print(f"诱导方向: {result.target_direction}")
        print(f"分析原因: {result.reasons}")
        print(f"风险警告: {result.warnings}")
        
        print(f"\n诱导信号: {detector.get_trap_signals()}")
