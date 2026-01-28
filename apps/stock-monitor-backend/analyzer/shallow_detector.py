"""
浅盘检测模块
检测亚盘盘口是否开得过浅，即盘口未能充分反映两队实力差距
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ShallowLevel(Enum):
    """浅盘程度枚举"""
    NOT_SHALLOW = "非浅盘"
    SLIGHTLY_SHALLOW = "轻微浅盘"
    MODERATELY_SHALLOW = "中度浅盘"
    VERY_SHALLOW = "深度浅盘"
    EXTREMELY_SHALLOW = "极度浅盘"


@dataclass
class ShallowAnalysisResult:
    """浅盘分析结果"""
    is_shallow: bool
    shallow_level: ShallowLevel
    shallow_score: float
    expected_handicap: float
    actual_handicap: float
    handicap_gap: float
    reasons: List[str]
    warnings: List[str]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_shallow': self.is_shallow,
            'shallow_level': self.shallow_level.value,
            'shallow_score': self.shallow_score,
            'expected_handicap': self.expected_handicap,
            'actual_handicap': self.actual_handicap,
            'handicap_gap': self.handicap_gap,
            'reasons': self.reasons,
            'warnings': self.warnings,
            'confidence': self.confidence,
        }


@dataclass
class CompanyShallowResult:
    """单家公司浅盘分析结果"""
    company: str
    is_shallow: bool
    expected_handicap: float
    actual_handicap: float
    handicap_gap: float
    water_difference: float


class ShallowDetector:
    """浅盘检测器"""
    
    def __init__(self, handicap_companies: List, team_comparison: Dict[str, Any]):
        self.handicap_companies = handicap_companies
        self.team_comparison = team_comparison
        self.expected_handicap = team_comparison.get('expected_handicap', 1.5)
        self.strength_diff = team_comparison.get('strength_diff', 30.0)
    
    def analyze(self) -> ShallowAnalysisResult:
        """执行浅盘分析"""
        company_results = self._analyze_all_companies()
        overall_result = self._calculate_overall_shallow_risk(company_results)
        
        return overall_result
    
    def _analyze_all_companies(self) -> List[CompanyShallowResult]:
        """分析所有公司的盘口"""
        results = []
        
        major_companies = ['澳门', 'bet365', '威廉希尔', '立博', '皇冠', '平均指数']
        
        for company in self.handicap_companies:
            company_name = company.company
            
            if not any(major in company_name for major in major_companies):
                continue
            
            expected = self._get_expected_pan_for_company(company_name)
            actual = company.latest_pan
            gap = expected - actual
            
            water_home = company.latest_home
            water_away = company.latest_away
            water_diff = abs(water_home - water_away)
            
            result = CompanyShallowResult(
                company=company_name,
                is_shallow=gap > 0.25,
                expected_handicap=expected,
                actual_handicap=actual,
                handicap_gap=gap,
                water_difference=water_diff
            )
            results.append(result)
        
        return results
    
    def _get_expected_pan_for_company(self, company_name: str) -> float:
        """根据公司特性获取预期盘口"""
        base_pan = self.expected_handicap
        
        conservative_companies = ['澳门', '香港马会']
        aggressive_companies = ['bet365', '立博']
        
        if any(c in company_name for c in conservative_companies):
            return base_pan - 0.1
        elif any(c in company_name for c in aggressive_companies):
            return base_pan + 0.1
        else:
            return base_pan
    
    def _calculate_overall_shallow_risk(self, company_results: List[CompanyShallowResult]) -> ShallowAnalysisResult:
        """计算整体浅盘风险"""
        if not company_results:
            return ShallowAnalysisResult(
                is_shallow=False,
                shallow_level=ShallowLevel.NOT_SHALLOW,
                shallow_score=0.0,
                expected_handicap=self.expected_handicap,
                actual_handicap=0.0,
                handicap_gap=0.0,
                reasons=[],
                warnings=["无法获取足够盘口数据进行分析"],
                confidence=0.5
            )
        
        gaps = [r.handicap_gap for r in company_results]
        avg_gap = sum(gaps) / len(gaps) if gaps else 0.0
        
        shallow_companies = sum(1 for r in company_results if r.is_shallow)
        shallow_ratio = shallow_companies / len(company_results) if company_results else 0
        
        water_diffs = [r.water_difference for r in company_results if r.actual_handicap > 0]
        avg_water_diff = sum(water_diffs) / len(water_diffs) if water_diffs else 0.15
        
        reasons = []
        warnings = []
        
        avg_gap_float = float(avg_gap) if not isinstance(avg_gap, (int, float)) else avg_gap
        
        if avg_gap_float > 0.5:
            shallow_score = min(100, 50 + avg_gap_float * 20)
            shallow_level = ShallowLevel.EXTREMELY_SHALLOW
            reasons.append(f"多家公司盘口明显偏浅，平均差距达{avg_gap_float:.2f}球")
        elif avg_gap_float > 0.35:
            shallow_score = min(100, 40 + avg_gap_float * 25)
            shallow_level = ShallowLevel.VERY_SHALLOW
            reasons.append(f"盘口深度不足，与预期差距{avg_gap_float:.2f}球")
        elif avg_gap_float > 0.2:
            shallow_score = min(100, 30 + avg_gap_float * 30)
            shallow_level = ShallowLevel.MODERATELY_SHALLOW
            reasons.append(f"盘口略浅，存在一定差距{avg_gap_float:.2f}球")
        elif avg_gap_float > 0.1:
            shallow_score = min(100, 20 + avg_gap_float * 40)
            shallow_level = ShallowLevel.SLIGHTLY_SHALLOW
            warnings.append(f"盘口轻微偏浅，差距{avg_gap_float:.2f}球")
        else:
            shallow_score = min(100, max(0, 20 - avg_gap * 20))
            shallow_level = ShallowLevel.NOT_SHALLOW
        
        if shallow_ratio > 0.6:
            warnings.append(f"{shallow_ratio*100:.0f}%的主流公司都开浅盘，需警惕")
        
        if avg_water_diff > 0.35:
            warnings.append(f"主客胜水位差过大（{avg_water_diff:.2f}），可能存在异常")
        
        if self.strength_diff > 40:
            if avg_gap > 0.3:
                reasons.append(f"主队实力明显占优（差距{self.strength_diff:.0f}分），但盘口未能充分体现")
        
        actual_handicap = sum(r.actual_handicap for r in company_results) / len(company_results)
        confidence = min(0.95, 0.6 + len(company_results) * 0.05)
        
        return ShallowAnalysisResult(
            is_shallow=shallow_score > 40,
            shallow_level=shallow_level,
            shallow_score=shallow_score,
            expected_handicap=self.expected_handicap,
            actual_handicap=actual_handicap,
            handicap_gap=avg_gap,
            reasons=reasons,
            warnings=warnings,
            confidence=confidence
        )
    
    def analyze_by_position(self) -> Dict[str, CompanyShallowResult]:
        """按盘口位置分析浅盘情况"""
        position_results = {}
        
        for company in self.handicap_companies:
            company_name = company.company
            actual = company.latest_pan
            
            if actual <= 0.5:
                position = "半球及以下"
            elif actual <= 1.0:
                position = "一球盘"
            elif actual <= 1.5:
                position = "球半盘"
            elif actual <= 2.0:
                position = "两球盘"
            else:
                position = "两球以上"
            
            if position not in position_results:
                expected = self._get_expected_pan_for_company(company_name)
                position_results[position] = CompanyShallowResult(
                    company=f"{position}平均",
                    is_shallow=expected - actual > 0.25,
                    expected_handicap=expected,
                    actual_handicap=actual,
                    handicap_gap=expected - actual,
                    water_difference=abs(company.latest_home - company.latest_away)
                )
        
        return position_results
    
    def get_shallow_indicators(self) -> Dict[str, Any]:
        """获取浅盘关键指标"""
        return {
            'strength_diff': self.strength_diff,
            'expected_handicap': self.expected_handicap,
            'handicap_coverage_rate': self._calculate_coverage_rate(),
            'water_imbalance_index': self._calculate_water_imbalance(),
            'company_consensus': self._calculate_company_consensus(),
        }
    
    def _calculate_coverage_rate(self) -> float:
        """计算盘口覆盖率（实际盘口/预期盘口）"""
        if not self.handicap_companies:
            return 1.0
        
        actual_pans = [c.latest_pan for c in self.handicap_companies if c.latest_pan > 0]
        if not actual_pans:
            return 1.0
        
        avg_actual = sum(actual_pans) / len(actual_pans)
        return avg_actual / self.expected_handicap if self.expected_handicap > 0 else 1.0
    
    def _calculate_water_imbalance(self) -> float:
        """计算水位失衡指数"""
        water_diffs = []
        
        for company in self.handicap_companies:
            if company.latest_home > 0 and company.latest_away > 0:
                diff = abs(company.latest_home - company.latest_away)
                water_diffs.append(diff)
        
        if not water_diffs:
            return 0.0
        
        avg_diff = sum(water_diffs) / len(water_diffs)
        return min(1.0, avg_diff / 0.4)
    
    def _calculate_company_consensus(self) -> float:
        """计算公司间共识度（盘口一致性）"""
        if len(self.handicap_companies) < 2:
            return 1.0
        
        pans = [c.latest_pan for c in self.handicap_companies if c.latest_pan > 0]
        if len(pans) < 2:
            return 1.0
        
        avg = sum(pans) / len(pans)
        variance = sum((p - avg) ** 2 for p in pans) / len(pans)
        std_dev = variance ** 0.5
        
        return max(0.0, 1.0 - std_dev / avg)


def analyze_shallow_odds(data_loader, team_comparison: Dict[str, Any]) -> ShallowAnalysisResult:
    """便捷函数：分析盘口是否过浅"""
    detector = ShallowDetector(
        handicap_companies=data_loader.handicap_companies,
        team_comparison=team_comparison
    )
    
    result = detector.analyze()
    result_dict = result.to_dict()
    
    return result


if __name__ == "__main__":
    from data_loader import DataLoader
    from team_analyzer import calculate_team_strength
    
    loader = DataLoader("/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/processed_samples/1314249.json")
    if loader.load():
        _, _, comparison = calculate_team_strength(loader)
        
        print("\n=== 浅盘分析 ===")
        detector = ShallowDetector(
            handicap_companies=loader.handicap_companies,
            team_comparison=comparison.to_dict()
        )
        
        result = detector.analyze()
        print(f"浅盘程度: {result.shallow_level.value}")
        print(f"浅盘评分: {result.shallow_score:.1f}")
        print(f"预期盘口: {result.expected_handicap:.2f}")
        print(f"实际盘口: {result.actual_handicap:.2f}")
        print(f"盘口差距: {result.handicap_gap:.2f}")
        print(f"分析原因: {result.reasons}")
        print(f"风险警告: {result.warnings}")
