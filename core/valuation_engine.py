"""
估值引擎 - 价值投资分析系统
支持: Graham Number / EPV / DCF / 历史百分位
作者: Faria
"""

import logging
import numpy as np
from typing import Optional, Dict
from dataclasses import dataclass

from core.data_collector import FinancialData

logger = logging.getLogger(__name__)


@dataclass
class ValuationResult:
    """估值结果"""
    code: str
    current_price: float
    
    # 各模型估值
    graham_value: Optional[float] = None
    epv_value: Optional[float] = None
    dcf_value: Optional[float] = None
    
    # 估值区间
    fair_value_low: Optional[float] = None
    fair_value_mid: Optional[float] = None
    fair_value_high: Optional[float] = None
    
    # 安全边际
    margin_of_safety: Optional[float] = None
    
    # 历史百分位评价
    pe_percentile_comment: str = ""
    
    # 评分
    valuation_score: int = 0
    signal: str = "HOLD"
    
    def to_dict(self) -> Dict:
        return {
            'code': self.code,
            'current_price': self.current_price,
            'graham_value': self.graham_value,
            'epv_value': self.epv_value,
            'dcf_value': self.dcf_value,
            'fair_value_low': self.fair_value_low,
            'fair_value_mid': self.fair_value_mid,
            'fair_value_high': self.fair_value_high,
            'margin_of_safety': self.margin_of_safety,
            'pe_percentile_comment': self.pe_percentile_comment,
            'valuation_score': self.valuation_score,
            'signal': self.signal
        }


class ValuationEngine:
    """估值引擎"""
    
    def __init__(self, risk_free_rate: float = 0.025):
        self.risk_free_rate = risk_free_rate
        self.wacc = 0.08  # 加权平均资本成本
    
    def calculate_graham_number(self, eps: float, bvps: float) -> Optional[float]:
        """
        Graham Number 计算
        公式: √(22.5 × EPS × 每股净资产)
        """
        if eps is None or bvps is None or eps <= 0 or bvps <= 0:
            return None
        return np.sqrt(22.5 * eps * bvps)
    
    def calculate_epv(self, adjusted_earnings_per_share: float,
                      growth_rate: float = 0.02) -> Optional[float]:
        """
        EPV (Earnings Power Value) 盈利能力价值
        公式: 调整后每股净利润 / (无风险利率 - 永续增长率)
        """
        if adjusted_earnings_per_share is None or adjusted_earnings_per_share <= 0:
            return None
        denominator = self.risk_free_rate - growth_rate
        if denominator <= 0:
            denominator = 0.03  # 保庖3%差值
        return adjusted_earnings_per_share / denominator
    
    def calculate_dcf_simple(self, fcf_per_share: float,
                             growth_5y: float = 0.10,
                             growth_terminal: float = 0.025) -> Optional[float]:
        """
        简化DCF计算（每股自由现金流折现）
        """
        if fcf_per_share is None or fcf_per_share <= 0:
            return None
        
        # 未来5年现金流折现
        pv_fcf = 0
        fcf = fcf_per_share
        for year in range(1, 6):
            fcf = fcf * (1 + growth_5y)
            pv_fcf += fcf / (1 + self.wacc) ** year
        
        # 终值
        terminal_fcf = fcf * (1 + growth_terminal)
        terminal_value = terminal_fcf / (self.wacc - growth_terminal)
        pv_terminal = terminal_value / (1 + self.wacc) ** 5
        
        return pv_fcf + pv_terminal
    
    def evaluate(self, data: FinancialData) -> ValuationResult:
        """
        综合估值分析
        """
        result = ValuationResult(
            code=data.code,
            current_price=data.current_price
        )
        
        values = []
        weights = []
        
        # 1. Graham Number (权重25%)
        if data.pe_ttm and data.pb and data.current_price > 0:
            eps = data.current_price / data.pe_ttm
            bvps = data.current_price / data.pb
            graham = self.calculate_graham_number(eps, bvps)
            if graham:
                result.graham_value = graham
                values.append(graham)
                weights.append(0.25)
        
        # 2. EPV (权重25%)
        if data.roe and data.pb and data.current_price > 0:
            book_value = data.current_price / data.pb
            adjusted_earnings = (data.roe / 100) * book_value
            epv = self.calculate_epv(adjusted_earnings)
            if epv:
                result.epv_value = epv
                values.append(epv)
                weights.append(0.25)
        
        # 3. 历史PE锚定 (权重25%)
        if data.pe_ttm and data.pe_median_5y and data.pe_median_5y > 0:
            eps = data.current_price / data.pe_ttm
            historical_value = eps * data.pe_median_5y
            values.append(historical_value)
            weights.append(0.25)
        
        # 4. 简化DCF (权重25%)
        if data.free_cash_flow and data.market_cap and data.market_cap > 0:
            # 简化：假设总股本 = 市值/PB/10（粗略估算）
            if data.pb and data.pb > 0:
                shares = data.market_cap / data.pb / 10  # 粗略估算
                if shares > 0:
                    fcf_per_share = data.free_cash_flow * 1e8 / (shares * 1e8)
                    dcf = self.calculate_dcf_simple(fcf_per_share)
                    if dcf:
                        result.dcf_value = dcf
                        values.append(dcf)
                        weights.append(0.25)
        
        # 计算加权公允价值
        if values and weights and sum(weights) > 0:
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            weighted_avg = sum(v * w for v, w in zip(values, normalized_weights))
            
            result.fair_value_low = min(values) * 0.9
            result.fair_value_mid = weighted_avg
            result.fair_value_high = max(values) * 1.1
            
            # 安全边际
            if weighted_avg > 0 and data.current_price > 0:
                result.margin_of_safety = (weighted_avg - data.current_price) / weighted_avg * 100
                
                # 估值评分
                if result.margin_of_safety >= 50:
                    result.valuation_score = 95
                elif result.margin_of_safety >= 30:
                    result.valuation_score = 85
                elif result.margin_of_safety >= 15:
                    result.valuation_score = 75
                elif result.margin_of_safety >= 0:
                    result.valuation_score = 65
                elif result.margin_of_safety >= -15:
                    result.valuation_score = 45
                else:
                    result.valuation_score = 25
                
                # 生成信号
                if result.margin_of_safety >= 30 and data.roe and data.roe > 15:
                    result.signal = "STRONG_BUY"
                elif result.margin_of_safety >= 15:
                    result.signal = "BUY"
                elif result.margin_of_safety >= 0:
                    result.signal = "HOLD"
                elif result.margin_of_safety >= -20:
                    result.signal = "OBSERVE"
                else:
                    result.signal = "SELL"
        
        # 历史PE百分位评价
        if data.pe_percentile is not None:
            if data.pe_percentile < 20:
                result.pe_percentile_comment = "历史低位，估值极低"
            elif data.pe_percentile < 40:
                result.pe_percentile_comment = "历史偏低，估值合理"
            elif data.pe_percentile < 60:
                result.pe_percentile_comment = "历史中位，估值合理"
            elif data.pe_percentile < 80:
                result.pe_percentile_comment = "历史偏高，注意风险"
            else:
                result.pe_percentile_comment = "历史高位，估值偏高"
        
        return result
