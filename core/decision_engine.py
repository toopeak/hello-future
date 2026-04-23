"""
决策引擎 - Buffett-Munger 价值投资框架
作者: Faria
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from core.data_collector import FinancialData
from core.valuation_engine import ValuationResult

logger = logging.getLogger(__name__)


@dataclass
class BuffettAnalysis:
    """Buffett视角分析"""
    moat_assessment: str = ""  # 护城河评估
    moat_score: int = 0  # 0-100
    
    financial_health: str = ""  # 财务健康评估
    financial_score: int = 0
    
    management_quality: str = ""  # 管理层评估
    management_score: int = 0
    
    consistency: str = ""  # 一致性评估（盈利稳定性）
    consistency_score: int = 0
    
    circle_of_competence: str = ""  # 能力圈评估
    
    verdict: str = ""  # Buffett结论


@dataclass
class MungerAnalysis:
    """Munger视角分析"""
    business_quality: str = ""  # 企业质量
    business_score: int = 0
    
    long_term_outlook: str = ""  # 长期前景
    
    mental_model_fit: str = ""  # 多元思维模型匹配度
    
    invert_thinking: str = ""  # 反过来想
    
    verdict: str = ""  # Munger结论


@dataclass
class FinalAnalysis:
    """最终分析结果"""
    code: str
    name: str
    market: str
    current_price: float
    currency: str
    
    # 估值结果
    valuation: ValuationResult
    
    # 专家视角
    buffett: BuffettAnalysis
    munger: MungerAnalysis
    
    # 综合评分
    total_score: int = 0
    signal: str = "HOLD"
    confidence: str = "中"
    
    # 操作建议
    recommendation: str = ""
    position_sizing: str = ""  # 仓位建议
    
    # 风险与机会
    risk_factors: List[str] = None
    opportunity_factors: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.opportunity_factors is None:
            self.opportunity_factors = []


class DecisionEngine:
    """Buffett-Munger决策引擎"""
    
    def __init__(self):
        self.weights = {
            'valuation': 0.30,      # 估值 30%
            'moat': 0.25,           # 护城河 25%
            'financial': 0.20,      # 财务健康 20%
            'management': 0.10,     # 管理层 10%
            'consistency': 0.10,    # 一致性 10%
            'business_quality': 0.05  # 企业质量 5%
        }
    
    def _analyze_moat(self, data: FinancialData) -> BuffettAnalysis:
        """分析护城河"""
        analysis = BuffettAnalysis()
        
        # 基于ROE和利润率评估护城河
        if data.roe and data.roe >= 20:
            analysis.moat_assessment = "强护城河：ROE持续超过20%，说明企业具有显著的竞争优势"
            analysis.moat_score = 90
        elif data.roe and data.roe >= 15:
            analysis.moat_assessment = "中等护城河：ROE在15-20%之间，具有一定竞争优势"
            analysis.moat_score = 75
        elif data.roe and data.roe >= 10:
            analysis.moat_assessment = "弱护城河：ROE在10-15%之间，竞争优势不明显"
            analysis.moat_score = 55
        else:
            analysis.moat_assessment = "无明显护城河：ROE低于10%，缺乏竞争优势"
            analysis.moat_score = 35
        
        # 毛利率补充
        if data.gross_margin and data.gross_margin >= 40:
            analysis.moat_score = min(100, analysis.moat_score + 5)
        
        return analysis
    
    def _analyze_financial(self, data: FinancialData) -> BuffettAnalysis:
        """分析财务健康"""
        analysis = BuffettAnalysis()
        scores = []
        comments = []
        
        # 负债率
        if data.debt_ratio:
            if data.debt_ratio < 40:
                scores.append(90)
                comments.append("负债率低（<40%），财务稳健")
            elif data.debt_ratio < 60:
                scores.append(70)
                comments.append("负债率适中（40-60%）")
            else:
                scores.append(40)
                comments.append("负债率偏高（>60%），需注意风险")
        
        # 流动比率
        if data.current_ratio:
            if data.current_ratio > 2:
                scores.append(90)
                comments.append("流动比率>2，短期偿债能力强")
            elif data.current_ratio > 1.5:
                scores.append(75)
                comments.append("流动比率>1.5，偿债能力良好")
            else:
                scores.append(50)
                comments.append("流动比率偏低，关注流动性")
        
        # 现金流
        if data.free_cash_flow and data.operating_cash_flow:
            if data.free_cash_flow > 0 and data.operating_cash_flow > 0:
                scores.append(85)
                comments.append("现金流为正，经营健康")
            else:
                scores.append(50)
                comments.append("现金流为负，资本开支大")
        
        if scores:
            analysis.financial_score = sum(scores) // len(scores)
            analysis.financial_health = "；".join(comments)
        else:
            analysis.financial_score = 50
            analysis.financial_health = "财务数据不足，无法完整评估"
        
        return analysis
    
    def _analyze_management(self, data: FinancialData) -> BuffettAnalysis:
        """分析管理层（基于可获取的财务数据推断）"""
        analysis = BuffettAnalysis()
        
        # 资本配置效率：ROE vs ROA
        if data.roe and data.roa:
            spread = data.roe - data.roa
            if spread < 5:
                analysis.management_score = 85
                analysis.management_quality = "资本配置保守，较少依赖杠杆，管理层稳健"
            elif spread < 10:
                analysis.management_score = 70
                analysis.management_quality = "适度使用杠杆，资本配置合理"
            else:
                analysis.management_score = 55
                analysis.management_quality = "杠杆使用较多，需关注资本配置效率"
        else:
            analysis.management_score = 60
            analysis.management_quality = "数据不足，无法评估管理层"
        
        return analysis
    
    def _analyze_consistency(self, data: FinancialData) -> BuffettAnalysis:
        """分析盈利一致性"""
        analysis = BuffettAnalysis()
        
        if data.revenue_growth_3y and data.profit_growth_3y:
            if data.revenue_growth_3y > 0 and data.profit_growth_3y > 0:
                if data.profit_growth_3y > data.revenue_growth_3y:
                    analysis.consistency_score = 85
                    analysis.consistency = "利润增速高于收入增速，规模效应显现，经营效率提升"
                else:
                    analysis.consistency_score = 75
                    analysis.consistency = "收入和利润同步增长，经营稳定"
            elif data.profit_growth_3y > 0:
                analysis.consistency_score = 60
                analysis.consistency = "利润增长但收入承压，需关注增长质量"
            else:
                analysis.consistency_score = 40
                analysis.consistency = "利润下滑，经营面临挑战"
        else:
            analysis.consistency_score = 50
            analysis.consistency = "增长数据不足"
        
        return analysis
    
    def _analyze_buffett(self, data: FinancialData) -> BuffettAnalysis:
        """Buffett综合分析"""
        moat = self._analyze_moat(data)
        financial = self._analyze_financial(data)
        management = self._analyze_management(data)
        consistency = self._analyze_consistency(data)
        
        # 综合Buffett视角
        buffett = BuffettAnalysis()
        buffett.moat_assessment = moat.moat_assessment
        buffett.moat_score = moat.moat_score
        buffett.financial_health = financial.financial_health
        buffett.financial_score = financial.financial_score
        buffett.management_quality = management.management_quality
        buffett.management_score = management.management_score
        buffett.consistency = consistency.consistency
        buffett.consistency_score = consistency.consistency_score
        
        # 能力圈评估
        if data.market_cap and data.market_cap > 1000:
            buffett.circle_of_competence = "大型企业，业务复杂，可能超出一般投资者能力圈"
        elif data.market_cap and data.market_cap > 100:
            buffett.circle_of_competence = "中型企业，业务相对清晰，能力圈内"
        else:
            buffett.circle_of_competence = "小型企业，研究覆盖少，需谨慎"
        
        return buffett
    
    def _analyze_munger(self, data: FinancialData, valuation: ValuationResult) -> MungerAnalysis:
        """Munger综合分析"""
        munger = MungerAnalysis()
        
        # 企业质量
        if data.roe and data.roe >= 15 and data.gross_margin and data.gross_margin >= 30:
            munger.business_quality = "高质量企业：高ROE + 高毛利率，具备定价权"
            munger.business_score = 85
        elif data.roe and data.roe >= 10:
            munger.business_quality = "中等质量企业：ROE达标但护城河不够深"
            munger.business_score = 65
        else:
            munger.business_quality = "普通企业：缺乏显著的竞争优势"
            munger.business_score = 45
        
        # 长期前景
        if data.revenue_growth_3y and data.revenue_growth_3y > 10:
            munger.long_term_outlook = "成长性良好，长期前景乐观"
        elif data.revenue_growth_3y and data.revenue_growth_3y > 0:
            munger.long_term_outlook = "低速增长，需关注行业天花板"
        else:
            munger.long_term_outlook = "增长停滞或下滑，长期前景存疑"
        
        # 反过来想
        if valuation.margin_of_safety and valuation.margin_of_safety < 0:
            munger.invert_thinking = f"反过来想：如果买入后股价下跌30%，PE将降至{data.pe_ttm * 0.7:.1f}x，是否仍然愿意持有？"
        else:
            munger.invert_thinking = "当前估值提供一定安全边际，下行风险可控"
        
        return munger
    
    def analyze(self, data: FinancialData, valuation: ValuationResult) -> FinalAnalysis:
        """
        执行完整分析
        """
        buffett = self._analyze_buffett(data)
        munger = self._analyze_munger(data, valuation)
        
        # 计算综合评分
        total = (
            valuation.valuation_score * self.weights['valuation'] +
            buffett.moat_score * self.weights['moat'] +
            buffett.financial_score * self.weights['financial'] +
            buffett.management_score * self.weights['management'] +
            buffett.consistency_score * self.weights['consistency'] +
            munger.business_score * self.weights['business_quality']
        )
        
        # 确定信号
        if valuation.signal == "STRONG_BUY" and buffett.moat_score >= 75:
            signal = "STRONG_BUY"
            confidence = "高"
        elif valuation.signal in ["BUY", "STRONG_BUY"]:
            signal = "BUY"
            confidence = "中高"
        elif valuation.signal == "HOLD" and buffett.moat_score >= 70:
            signal = "HOLD"
            confidence = "中"
        elif valuation.signal == "HOLD":
            signal = "OBSERVE"
            confidence = "中"
        elif valuation.signal == "SELL":
            signal = "SELL"
            confidence = "高"
        else:
            signal = "OBSERVE"
            confidence = "低"
        
        # 生成操作建议
        if signal in ["STRONG_BUY", "BUY"]:
            if valuation.margin_of_safety and valuation.margin_of_safety >= 30:
                position = "可建50-70%仓位"
            else:
                position = "可建30-50%仓位，回调加仓"
        elif signal == "HOLD":
            position = "持有现有仓位，暂不增仓"
        elif signal == "OBSERVE":
            position = "空仓观察，等待更好价格"
        else:
            position = "考虑减仓或清仓"
        
        # 生成风险与机会
        risks = []
        opportunities = []
        
        if valuation.margin_of_safety and valuation.margin_of_safety < 0:
            risks.append("估值偏高，安全边际不足")
        if buffett.moat_score < 60:
            risks.append("护城河较弱，竞争优势不明显")
        if data.debt_ratio and data.debt_ratio > 60:
            risks.append("负债率偏高，财务风险需关注")
        
        if valuation.margin_of_safety and valuation.margin_of_safety > 15:
            opportunities.append("估值合理，具备安全边际")
        if buffett.moat_score >= 80:
            opportunities.append("护城河深厚，具备长期竞争优势")
        if data.roe and data.roe >= 15:
            opportunities.append("ROE优秀，盈利能力强劲")
        
        return FinalAnalysis(
            code=data.code,
            name=data.name,
            market=data.market,
            current_price=data.current_price,
            currency=data.currency,
            valuation=valuation,
            buffett=buffett,
            munger=munger,
            total_score=int(total),
            signal=signal,
            confidence=confidence,
            recommendation=position,
            position_sizing=position,
            risk_factors=risks,
            opportunity_factors=opportunities
        )
