"""
增强版飞书推送模块 - 更丰富的价值投资维度
作者: Faria
版本: v2.1
"""

import json
import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class HistoricalValuation:
    """历史估值数据"""
    pe_min: float
    pe_max: float
    pe_median: float
    pe_avg: float
    pe_percentile: float  # 当前PE在历史区间中的百分位
    
    pb_min: float
    pb_max: float
    pb_median: float
    pb_avg: float
    pb_percentile: float
    
    ps_min: Optional[float] = None
    ps_max: Optional[float] = None
    ps_median: Optional[float] = None
    
    # 5年分位
    pe_5y_low: Optional[float] = None
    pe_5y_high: Optional[float] = None


@dataclass
class IndustryComparison:
    """行业对比数据"""
    industry_name: str
    industry_avg_pe: float
    industry_avg_pb: float
    industry_avg_roe: float
    
    pe_premium: float  # PE溢价率 (当前PE/行业平均-1)
    pb_premium: float
    roe_premium: float
    
    ranking_in_industry: int  # 行业内排名
    total_in_industry: int


@dataclass
class QualityBreakdown:
    """质量评分细分"""
    profitability_score: int  # 盈利能力 0-100
    growth_score: int         # 成长性 0-100
    financial_health_score: int  # 财务健康 0-100
    stability_score: int      # 稳定性 0-100
    management_score: int     # 管理层 0-100
    moat_score: int          # 护城河 0-100


@dataclass
class EnhancedStockAnalysis:
    """增强版股票分析结果"""
    code: str
    name: str
    market: str
    current_price: float
    currency: str
    
    # 基础估值
    pe_ttm: Optional[float] = None
    forward_pe: Optional[float] = None
    pb: Optional[float] = None
    ps: Optional[float] = None
    peg: Optional[float] = None
    ev_ebitda: Optional[float] = None
    dividend_yield: Optional[float] = None
    
    # 财务指标
    roe: Optional[float] = None
    roa: Optional[float] = None
    profit_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    debt_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None  # 利息保障倍数
    
    # 成长性
    revenue_growth_3y: Optional[float] = None  # 3年营收复合增长
    profit_growth_3y: Optional[float] = None
    fcf_growth_3y: Optional[float] = None
    
    # 现金流
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    fcf_yield: Optional[float] = None  # FCF/市值
    
    # 估值模型结果
    graham_value: Optional[float] = None
    epv_value: Optional[float] = None
    dcf_value: Optional[float] = None
    margin_of_safety: Optional[float] = None
    
    # 历史估值
    historical: Optional[HistoricalValuation] = None
    
    # 行业对比
    industry: Optional[IndustryComparison] = None
    
    # 质量细分
    quality: Optional[QualityBreakdown] = None
    total_score: int = 0
    signal: str = "HOLD"
    
    # 分析师预期
    analyst_target: Optional[float] = None
    upside: Optional[float] = None
    
    # 风险与机会
    risk_factors: List[str] = None
    opportunity_factors: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.opportunity_factors is None:
            self.opportunity_factors = []


class EnhancedFeishuNotifier:
    """增强版飞书通知器"""
    
    def __init__(self, webhook_url: str, timeout: int = 10):
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def _send(self, payload: Dict) -> Dict:
        try:
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                logger.error(f"飞书API错误: {result}")
                return {"success": False, "error": result.get("msg", "未知错误")}
            
            return {"success": True, "data": result}
            
        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def _get_signal_display(self, signal: str) -> tuple:
        """获取信号显示配置"""
        signal_map = {
            "STRONG_BUY": ("强烈买入", "red", "🔴"),
            "BUY": ("买入", "green", "🟢"),
            "HOLD": ("持有", "blue", "🟡"),
            "OBSERVE": ("观察", "orange", "👁️"),
            "REDUCE": ("减仓", "orange", "⚠️"),
            "SELL": ("卖出", "red", "🔴")
        }
        return signal_map.get(signal, (signal, "blue", "➖"))
    
    def _format_value(self, val, suffix="", default="--"):
        if val is None:
            return default
        return f"{val:.2f}{suffix}"
    
    def send_enhanced_analysis_card(self, analysis: EnhancedStockAnalysis) -> Dict:
        """
        发送增强版分析卡片 - 多维度价值投资分析
        """
        signal_text, color, emoji = self._get_signal_display(analysis.signal)
        
        # 构建字段列表
        fields = [
            # 第一行: 价格和基础估值
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**当前价格**\n{analysis.currency}**{analysis.current_price:.2f}**\n⭐ 综合评分: {analysis.total_score}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**PE(TTM)**\n{self._format_value(analysis.pe_ttm, 'x')}\n**Forward PE**\n{self._format_value(analysis.forward_pe, 'x')}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**PB / PS**\n{self._format_value(analysis.pb, 'x')} / {self._format_value(analysis.ps, 'x')}\n**EV/EBITDA**\n{self._format_value(analysis.ev_ebitda, 'x')}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**股息率 / FCF Yield**\n{self._format_value(analysis.dividend_yield, '%')} / {self._format_value(analysis.fcf_yield, '%')}\n**PEG**\n{self._format_value(analysis.peg)}"
                }
            },
            # 第二行: 财务质量
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**ROE / ROA**\n{self._format_value(analysis.roe, '%')} / {self._format_value(analysis.roa, '%')}\n**净利率 / 毛利率**\n{self._format_value(analysis.profit_margin, '%')} / {self._format_value(analysis.gross_margin, '%')}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**经营利润率**\n{self._format_value(analysis.operating_margin, '%')}\n**负债率**\n{self._format_value(analysis.debt_ratio, '%')}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**流动比率**\n{self._format_value(analysis.current_ratio)}\n**利息保障**\n{self._format_value(analysis.interest_coverage, 'x')}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**经营现金流**\n{self._format_value(analysis.operating_cash_flow, '亿')}\n**自由现金流**\n{self._format_value(analysis.free_cash_flow, '亿')}"
                }
            },
            # 第三行: 成长性
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**3年营收增长**\n{self._format_value(analysis.revenue_growth_3y, '%')}\n**3年利润增长**\n{self._format_value(analysis.profit_growth_3y, '%')}"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**3年FCF增长**\n{self._format_value(analysis.fcf_growth_3y, '%')}"
                }
            },
        ]
        
        # 添加估值模型字段
        if analysis.graham_value or analysis.epv_value or analysis.dcf_value:
            valuation_fields = []
            if analysis.graham_value:
                valuation_fields.append(f"**Graham**: {analysis.currency}{analysis.graham_value:.1f}")
            if analysis.epv_value:
                valuation_fields.append(f"**EPV**: {analysis.currency}{analysis.epv_value:.1f}")
            if analysis.dcf_value:
                valuation_fields.append(f"**DCF**: {analysis.currency}{analysis.dcf_value:.1f}")
            
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(valuation_fields)
                }
            })
            
            if analysis.margin_of_safety is not None:
                mos_emoji = "✅" if analysis.margin_of_safety > 0 else "❌"
                fields.append({
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**安全边际**\n{mos_emoji} {analysis.margin_of_safety:.1f}%"
                    }
                })
        
        # 添加历史估值字段
        if analysis.historical:
            h = analysis.historical
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**历史PE区间**\n{h.pe_min:.1f}x ~ {h.pe_max:.1f}x\n**中位数**: {h.pe_median:.1f}x"
                }
            })
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**PE历史百分位**\n{h.pe_percentile:.0f}%\n{'🔴 高估' if h.pe_percentile > 70 else '🟡 合理' if h.pe_percentile > 30 else '🟢 低估'}"
                }
            })
        
        # 添加行业对比
        if analysis.industry:
            ind = analysis.industry
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**行业: {ind.industry_name}**\n行业平均PE: {ind.industry_avg_pe:.1f}x\n行业平均ROE: {ind.industry_avg_roe:.1f}%"
                }
            })
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**相对行业**\nPE溢价: {ind.pe_premium:+.1f}%\nROE溢价: {ind.roe_premium:+.1f}%\n排名: {ind.ranking_in_industry}/{ind.total_in_industry}"
                }
            })
        
        # 构建卡片元素
        elements = [
            {
                "tag": "div",
                "fields": fields
            }
        ]
        
        # 添加质量评分细分
        if analysis.quality:
            q = analysis.quality
            elements.append({
                "tag": "hr"
            })
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**质量评分细分** | 盈利:{q.profitability_score} 成长:{q.growth_score} 健康:{q.financial_health_score} 稳定:{q.stability_score} 管理:{q.management_score} 护城河:{q.moat_score}"
                }
            })
        
        # 添加分析师预期
        if analysis.analyst_target:
            upside_text = f"+{analysis.upside:.1f}%" if analysis.upside else ""
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**分析师共识目标价**: {analysis.currency}{analysis.analyst_target:.2f} ({upside_text})"
                }
            })
        
        # 添加风险因素
        if analysis.risk_factors:
            risk_text = "\n".join([f"- {r}" for r in analysis.risk_factors[:3]])
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**⚠️ 风险因素**\n{risk_text}"
                }
            })
        
        # 添加机会因素
        if analysis.opportunity_factors:
            opp_text = "\n".join([f"+ {o}" for o in analysis.opportunity_factors[:3]])
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**✅ 机会因素**\n{opp_text}"
                }
            })
        
        # 底部时间戳
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"---\n*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 价值投资分析系统 v2.1*"
            }
        })
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": color,
                    "title": {
                        "tag": "plain_text",
                        "content": f"{emoji} {signal_text} | {analysis.name} ({analysis.code})"
                    }
                },
                "elements": elements
            }
        }
        
        return self._send(payload)
    
    def send_multi_dimension_report(self, analyses: List[EnhancedStockAnalysis]) -> Dict:
        """发送多维度对比报告"""
        if not analyses:
            return {"success": False, "error": "无分析数据"}
        
        # 分类
        buy_list = [a for a in analyses if a.signal in ["STRONG_BUY", "BUY"]]
        hold_list = [a for a in analyses if a.signal == "HOLD"]
        observe_list = [a for a in analyses if a.signal == "OBSERVE"]
        sell_list = [a for a in analyses if a.signal in ["REDUCE", "SELL"]]
        
        def build_section(title: str, stocks: List[EnhancedStockAnalysis], color: str) -> str:
            if not stocks:
                return ""
            lines = [f"\n{color} **{title}**"]
            for s in sorted(stocks, key=lambda x: x.total_score, reverse=True):
                mos = f"(安全边际{s.margin_of_safety:.0f}%)" if s.margin_of_safety else ""
                hist_pe = f"| PE百分位{s.historical.pe_percentile:.0f}%" if s.historical else ""
                lines.append(f"- {s.name}({s.code}): {s.currency}{s.current_price:.2f} | PE{s.pe_ttm:.1f}x {hist_pe} | 评分{s.total_score} {mos}")
            return "\n".join(lines)
        
        content = f"**共分析 {len(analyses)} 只股票** | 买入:{len(buy_list)} 持有:{len(hold_list)} 观察:{len(observe_list)} 卖出:{len(sell_list)}\n"
        content += build_section("买入机会", buy_list, "🟢")
        content += build_section("持有", hold_list, "🟡")
        content += build_section("观察", observe_list, "👁️")
        content += build_section("卖出", sell_list, "🔴")
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": "blue",
                    "title": {
                        "tag": "plain_text",
                        "content": f"📊 价值投资多维分析报告 | {datetime.now().strftime('%Y-%m-%d')}"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**分析维度**: PE/PB/PS/EV-EBITDA | Graham/EPV/DCF | 历史百分位 | 行业对比 | 质量评分 | 安全边际\n*数据来源: Yahoo Finance / AKShare*"
                        }
                    }
                ]
            }
        }
        
        return self._send(payload)
