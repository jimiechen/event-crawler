"""
核心分析模块
整合浅盘检测和诱导盘检测，提供综合分析报告
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class OverallRiskLevel(Enum):
    """整体风险等级"""
    VERY_LOW = "极低风险"
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"
    DANGER = "危险"


class BetRecommendation(Enum):
    """投注建议"""
    STRONG_HOME = "强烈建议主胜"
    HOME = "建议主胜"
    AVOID = "建议观望"
    AWAY = "建议客胜"
    STRONG_AWAY = "强烈建议客胜"
    DRAW = "建议平局"
    NO_RECOMMENDATION = "无明确建议"


@dataclass
class ComprehensiveAnalysis:
    """综合分析结果"""
    match_info: Dict[str, str]
    team_comparison: Dict[str, Any]
    shallow_analysis: Dict[str, Any]
    trap_analysis: Dict[str, Any]
    overall_risk: Dict[str, Any]
    recommendations: List[str]
    betting_suggestion: Dict[str, Any]
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'match_info': self.match_info,
            'team_comparison': self.team_comparison,
            'shallow_analysis': self.shallow_analysis,
            'trap_analysis': self.trap_analysis,
            'overall_risk': self.overall_risk,
            'recommendations': self.recommendations,
            'betting_suggestion': self.betting_suggestion,
            'analysis_timestamp': self.analysis_timestamp,
        }
    
    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class AnalysisReport:
    """分析报告"""
    title: str
    sections: List[Dict[str, Any]]
    conclusion: str
    confidence: float
    
    def format_report(self) -> str:
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  {self.title}")
        lines.append(f"{'='*60}\n")
        
        for section in self.sections:
            lines.append(f"【{section['title']}】")
            for item in section['content']:
                lines.append(f"  • {item}")
            lines.append("")
        
        lines.append(f"{'='*60}")
        lines.append(f"  结论: {self.conclusion}")
        lines.append(f"  置信度: {self.confidence:.1%}")
        lines.append(f"{'='*60}\n")
        
        return "\n".join(lines)


class HandicapAnalyzer:
    """盘口综合分析器"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.home_team = data_loader.match_info.home_team
        self.away_team = data_loader.match_info.away_team
        
        from team_analyzer import calculate_team_strength
        self.home_strength, self.away_strength, self.team_comparison = calculate_team_strength(data_loader)
    
    def analyze_comprehensive(self) -> ComprehensiveAnalysis:
        """执行综合分析"""
        from shallow_detector import ShallowDetector
        from trap_detector import TrapDetector
        
        shallow_detector = ShallowDetector(
            handicap_companies=self.data_loader.handicap_companies,
            team_comparison=self.team_comparison.to_dict()
        )
        shallow_result = shallow_detector.analyze()
        
        trap_detector = TrapDetector(
            handicap_companies=self.data_loader.handicap_companies,
            euro_companies=self.data_loader.euro_companies,
            exchanges=self.data_loader.exchanges,
            team_comparison=self.team_comparison.to_dict()
        )
        trap_result = trap_detector.analyze()
        
        overall_risk = self._assess_overall_risk(shallow_result, trap_result)
        recommendations = self._generate_recommendations(shallow_result, trap_result)
        betting_suggestion = self._generate_betting_suggestion(
            shallow_result, trap_result, overall_risk
        )
        
        match_info = {
            'match_id': self.data_loader.match_info.match_id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'league': self.data_loader.match_info.league,
            'score': self.data_loader.match_info.score_text,
        }
        
        return ComprehensiveAnalysis(
            match_info=match_info,
            team_comparison=self.team_comparison.to_dict(),
            shallow_analysis=shallow_result.to_dict(),
            trap_analysis=trap_result.to_dict(),
            overall_risk=overall_risk,
            recommendations=recommendations,
            betting_suggestion=betting_suggestion
        )
    
    def _assess_overall_risk(self, shallow_result, trap_result) -> Dict[str, Any]:
        """评估整体风险"""
        shallow_score = shallow_result.shallow_score
        trap_score = trap_result.trap_score
        
        combined_score = (shallow_score * 0.4 + trap_score * 0.6)
        
        if combined_score >= 80:
            risk_level = OverallRiskLevel.DANGER
        elif combined_score >= 65:
            risk_level = OverallRiskLevel.VERY_HIGH
        elif combined_score >= 50:
            risk_level = OverallRiskLevel.HIGH
        elif combined_score >= 35:
            risk_level = OverallRiskLevel.MEDIUM
        elif combined_score >= 20:
            risk_level = OverallRiskLevel.LOW
        else:
            risk_level = OverallRiskLevel.VERY_LOW
        
        risk_factors = []
        
        if shallow_score > 40:
            risk_factors.append(f"浅盘风险: {shallow_score:.0f}分")
        if trap_score > 40:
            risk_factors.append(f"诱导盘风险: {trap_score:.0f}分")
        
        confidence = (shallow_result.confidence + trap_result.confidence) / 2
        
        return {
            'risk_level': risk_level.value,
            'risk_score': combined_score,
            'shallow_score': shallow_score,
            'trap_score': trap_score,
            'risk_factors': risk_factors,
            'confidence': confidence,
            'analysis_quality': self._assess_analysis_quality(shallow_result, trap_result)
        }
    
    def _assess_analysis_quality(self, shallow_result, trap_result) -> str:
        """评估分析质量"""
        data_completeness = 0
        
        if len(self.data_loader.handicap_companies) >= 10:
            data_completeness += 0.3
        elif len(self.data_loader.handicap_companies) >= 5:
            data_completeness += 0.2
        
        if len(self.data_loader.euro_companies) >= 10:
            data_completeness += 0.3
        elif len(self.data_loader.euro_companies) >= 5:
            data_completeness += 0.2
        
        if self.data_loader.exchanges.get('five_factors'):
            data_completeness += 0.2
        
        data_completeness += (shallow_result.confidence + trap_result.confidence) / 2 * 0.3
        
        if data_completeness >= 0.85:
            return "高"
        elif data_completeness >= 0.70:
            return "较高"
        elif data_completeness >= 0.55:
            return "中等"
        else:
            return "较低"
    
    def _generate_recommendations(self, shallow_result, trap_result) -> List[str]:
        """生成分析建议"""
        recommendations = []
        
        if shallow_result.is_shallow:
            recommendations.append(f"⚠️ 浅盘警告: {shallow_result.shallow_level.value}")
            for reason in shallow_result.reasons[:3]:
                recommendations.append(f"  - {reason}")
        
        if trap_result.is_trap:
            recommendations.append(f"🚨 诱导盘警告: {trap_result.trap_type.value}")
            recommendations.append(f"  诱导方向: {trap_result.target_direction}")
            for reason in trap_result.reasons[:3]:
                recommendations.append(f"  - {reason}")
        
        if not shallow_result.is_shallow and not trap_result.is_trap:
            recommendations.append("✅ 盘口形态正常，未检测到明显异常")
        
        if shallow_result.warnings:
            recommendations.append("\n📋 风险提示:")
            for warning in shallow_result.warnings[:3]:
                recommendations.append(f"  • {warning}")
        
        if trap_result.warnings:
            recommendations.append("\n⚡ 诱导信号:")
            for warning in trap_result.warnings[:3]:
                recommendations.append(f"  • {warning}")
        
        return recommendations
    
    def _generate_betting_suggestion(self, shallow_result, trap_result, 
                                      overall_risk: Dict[str, Any]) -> Dict[str, Any]:
        """生成投注建议"""
        risk_score = overall_risk['risk_score']
        shallow_score = overall_risk['shallow_score']
        trap_score = overall_risk['trap_score']
        
        strength_diff = self.team_comparison.strength_diff
        
        if risk_score >= 70:
            suggestion = BetRecommendation.AVOID
            reason = "风险过高，建议观望"
        elif risk_score >= 50:
            if trap_result.target_direction == "诱导投注主胜":
                suggestion = BetRecommendation.AWAY
                reason = "检测到诱导主胜信号，可考虑反向下注"
            else:
                suggestion = BetRecommendation.NO_RECOMMENDATION
                reason = "存在诱导盘特征，建议谨慎"
        elif shallow_result.is_shallow:
            if shallow_result.handicap_gap > 0.3:
                suggestion = BetRecommendation.AWAY
                reason = "浅盘可能表明庄家对主队大胜信心不足"
            else:
                suggestion = BetRecommendation.HOME
                reason = "浅盘但风险可控，可考虑主胜"
        else:
            if strength_diff > 30:
                suggestion = BetRecommendation.HOME
                reason = "主队实力明显占优，可考虑主胜"
            elif strength_diff < -20:
                suggestion = BetRecommendation.AWAY
                reason = "客队有机会爆冷，可考虑客胜"
            else:
                suggestion = BetRecommendation.NO_RECOMMENDATION
                reason = "盘口合理，无明显投注价值"
        
        alternative_bets = []
        
        if trap_result.trap_indicators.get('asia_euro_score', 0) > 50:
            alternative_bets.append("亚欧走势矛盾，可考虑小球")
        
        if trap_result.trap_indicators.get('water_trap_score', 0) > 40:
            alternative_bets.append("水位异常，可考虑关注下盘")
        
        confidence = overall_risk['confidence']
        min_bet_odds = self._calculate_min_bet_odds(risk_score, confidence)
        
        return {
            'primary_suggestion': suggestion.value,
            'reason': reason,
            'alternative_bets': alternative_bets,
            'min_odds_requirement': min_bet_odds,
            'stake_recommendation': self._calculate_stake_recommendation(risk_score, confidence),
            'expected_value': self._calculate_expected_value(suggestion, risk_score, confidence),
        }
    
    def _calculate_min_bet_odds(self, risk_score: float, confidence: float) -> float:
        """计算最低投注赔率要求"""
        base_odds = 1.8
        
        risk_penalty = risk_score / 100 * 0.5
        
        confidence_bonus = confidence * 0.3
        
        return round(base_odds - risk_penalty + confidence_bonus, 2)
    
    def _calculate_stake_recommendation(self, risk_score: float, confidence: float) -> str:
        """计算建议投注金额比例"""
        if risk_score >= 70:
            return "0%（不建议投注）"
        elif risk_score >= 50:
            return "1-2%（小额试探）"
        elif risk_score >= 35:
            return "3-5%（正常投注）"
        elif risk_score >= 20:
            return "5-8%（适度重注）"
        else:
            return "8-10%（可以重注）"
    
    def _calculate_expected_value(self, suggestion: BetRecommendation, 
                                   risk_score: float, confidence: float) -> float:
        """计算预期价值"""
        if suggestion == BetRecommendation.AVOID:
            return -0.5
        
        base_ev = 0.5
        
        if suggestion in [BetRecommendation.STRONG_HOME, BetRecommendation.STRONG_AWAY]:
            base_ev += 0.3
        
        confidence_bonus = confidence * 0.2
        risk_penalty = risk_score / 100 * 0.3
        
        return round(base_ev + confidence_bonus - risk_penalty, 2)
    
    def generate_report(self, analysis: ComprehensiveAnalysis) -> AnalysisReport:
        """生成分析报告"""
        sections = []
        
        section1 = {
            'title': '基本信息',
            'content': [
                f"对阵: {analysis.match_info['home_team']} vs {analysis.match_info['away_team']}",
                f"联赛: {analysis.match_info['league']}",
                f"比分: {analysis.match_info['score']}",
                f"分析时间: {analysis.analysis_timestamp}",
            ]
        }
        sections.append(section1)
        
        section2 = {
            'title': '球队实力分析',
            'content': [
                f"实力差距: {self.team_comparison.strength_diff:.1f}分",
                f"主场优势: {self.team_comparison.home_advantage:.1f}分",
                f"预期盘口: {self.team_comparison.expected_handicap:.2f}球",
            ]
        }
        
        home_strength = analysis.team_comparison.get('home_strength', {})
        away_strength = analysis.team_comparison.get('away_strength', {})
        
        if home_strength:
            section2['content'].extend([
                f"主队综合: {home_strength.get('overall_score', 0):.1f}分",
                f"客队综合: {away_strength.get('overall_score', 0):.1f}分",
            ])
        
        sections.append(section2)
        
        section3 = {
            'title': '浅盘分析',
            'content': [
                f"浅盘程度: {analysis.shallow_analysis.get('shallow_level', '未知')}",
                f"浅盘评分: {analysis.shallow_analysis.get('shallow_score', 0):.1f}",
                f"预期盘口: {analysis.shallow_analysis.get('expected_handicap', 0):.2f}",
                f"实际盘口: {analysis.shallow_analysis.get('actual_handicap', 0):.2f}",
                f"盘口差距: {analysis.shallow_analysis.get('handicap_gap', 0):.2f}",
            ]
        }
        
        if analysis.shallow_analysis.get('reasons'):
            section3['content'].extend([f"  → {r}" for r in analysis.shallow_analysis['reasons'][:2]])
        
        sections.append(section3)
        
        section4 = {
            'title': '诱导盘分析',
            'content': [
                f"诱导类型: {analysis.trap_analysis.get('trap_type', '未知')}",
                f"诱导评分: {analysis.trap_analysis.get('trap_score', 0):.1f}",
                f"诱导方向: {analysis.trap_analysis.get('target_direction', '无')}",
            ]
        }
        
        trap_indicators = analysis.trap_analysis.get('trap_indicators', {})
        if trap_indicators:
            section4['content'].append("各指标评分:")
            for key, value in trap_indicators.items():
                section4['content'].append(f"  - {key}: {value:.1f}")
        
        if analysis.trap_analysis.get('reasons'):
            section4['content'].extend([f"  → {r}" for r in analysis.trap_analysis['reasons'][:2]])
        
        sections.append(section4)
        
        section5 = {
            'title': '整体评估',
            'content': [
                f"风险等级: {analysis.overall_risk.get('risk_level', '未知')}",
                f"风险评分: {analysis.overall_risk.get('risk_score', 0):.1f}",
                f"分析质量: {analysis.overall_risk.get('analysis_quality', '未知')}",
                f"置信度: {analysis.overall_risk.get('confidence', 0):.1%}",
            ]
        }
        
        if analysis.overall_risk.get('risk_factors'):
            section5['content'].append("风险因素:")
            for factor in analysis.overall_risk['risk_factors']:
                section5['content'].append(f"  ⚠️ {factor}")
        
        sections.append(section5)
        
        section6 = {
            'title': '投注建议',
            'content': [
                f"推荐方向: {analysis.betting_suggestion.get('primary_suggestion', '无')}",
                f"推荐理由: {analysis.betting_suggestion.get('reason', '无')}",
                f"最低赔率要求: {analysis.betting_suggestion.get('min_odds_requirement', 0):.2f}",
                f"建议投注比例: {analysis.betting_suggestion.get('stake_recommendation', '无')}",
                f"预期价值: {analysis.betting_suggestion.get('expected_value', 0):.2f}",
            ]
        }
        
        if analysis.betting_suggestion.get('alternative_bets'):
            section6['content'].append("备选方案:")
            for alt in analysis.betting_suggestion['alternative_bets']:
                section6['content'].append(f"  → {alt}")
        
        sections.append(section6)
        
        confidence = analysis.overall_risk.get('confidence', 0.5)
        
        if analysis.betting_suggestion.get('primary_suggestion') == '建议观望':
            conclusion = "盘口存在异常，建议谨慎观望"
        elif analysis.overall_risk.get('risk_score', 0) > 60:
            conclusion = "风险较高，建议减少投注或观望"
        elif analysis.betting_suggestion.get('primary_suggestion', '').startswith('建议'):
            conclusion = f"{analysis.betting_suggestion['primary_suggestion']}，{analysis.betting_suggestion['reason']}"
        else:
            conclusion = "盘口形态正常，可根据实际情况投注"
        
        return AnalysisReport(
            title=f"盘口分析报告 - {self.home_team} vs {self.away_team}",
            sections=sections,
            conclusion=conclusion,
            confidence=confidence
        )


def analyze_match(data_loader) -> Tuple[ComprehensiveAnalysis, AnalysisReport]:
    """便捷函数：分析单场比赛"""
    analyzer = HandicapAnalyzer(data_loader)
    analysis = analyzer.analyze_comprehensive()
    report = analyzer.generate_report(analysis)
    
    return analysis, report


if __name__ == "__main__":
    from data_loader import DataLoader
    
    loader = DataLoader("/Users/mac/StudioProjects/2026/open-citycloud-workspace/data/okooo/processed_samples/1314249.json")
    if loader.load():
        print("开始综合分析...")
        
        analysis, report = analyze_match(loader)
        
        print(report.format_report())
        
        print("\n详细JSON输出:")
        print(analysis.to_json())
