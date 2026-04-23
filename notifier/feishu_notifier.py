"""
飞书推送模块 - 价值投资分析系统
支持: 文本消息、Markdown、交互卡片、图片

作者: Faria
版本: v2.0
"""

import json
import logging
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class StockAnalysisResult:
    """股票分析结果数据结构"""
    code: str
    name: str
    market: str  # A股/港股/美股
    current_price: float
    currency: str
    
    # 估值指标
    pe_ttm: Optional[float] = None
    forward_pe: Optional[float] = None
    pb: Optional[float] = None
    ps: Optional[float] = None
    peg: Optional[float] = None
    dividend_yield: Optional[float] = None
    
    # 财务指标
    roe: Optional[float] = None
    roa: Optional[float] = None
    profit_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    debt_ratio: Optional[float] = None
    
    # 估值结果
    graham_value: Optional[float] = None
    epv_value: Optional[float] = None
    margin_of_safety: Optional[float] = None
    
    # 评分
    total_score: int = 0
    signal: str = "HOLD"  # STRONG_BUY/BUY/HOLD/OBSERVE/REDUCE/SELL
    
    # 目标价
    analyst_target: Optional[float] = None
    upside: Optional[float] = None
    
    # 风险
    risk_factors: List[str] = None
    opportunity_factors: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.opportunity_factors is None:
            self.opportunity_factors = []


class FeishuNotifier:
    """飞书通知器 - 支持多种消息格式"""
    
    def __init__(self, webhook_url: str, timeout: int = 10):
        """
        初始化
        
        Args:
            webhook_url: 飞书机器人webhook地址
            timeout: 请求超时时间(秒)
        """
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.session = requests.Session()
        
    def _send(self, payload: Dict) -> Dict:
        """发送消息到飞书"""
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
                logger.error(f"飞书API返回错误: {result}")
                return {"success": False, "error": result.get("msg", "未知错误")}
            
            logger.info("飞书推送成功")
            return {"success": True, "data": result}
            
        except requests.exceptions.Timeout:
            logger.error("飞书推送超时")
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.RequestException as e:
            logger.error(f"飞书推送失败: {e}")
            return {"success": False, "error": str(e)}
    
    def send_text(self, text: str) -> Dict:
        """发送简单文本消息"""
        payload = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        return self._send(payload)
    
    def send_markdown(self, title: str, content: str) -> Dict:
        """发送Markdown格式消息"""
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            [{"tag": "text", "text": content}]
                        ]
                    }
                }
            }
        }
        return self._send(payload)
    
    def send_stock_analysis_card(self, 
                                  analysis: StockAnalysisResult,
                                  template_color: str = "blue") -> Dict:
        """发送单股票分析卡片
        
        Args:
            analysis: 股票分析结果
            template_color: 卡片颜色 (blue/green/orange/red)
        """
        # 根据信号设置颜色
        color_map = {
            "STRONG_BUY": "green",
            "BUY": "green",
            "HOLD": "blue",
            "OBSERVE": "orange",
            "REDUCE": "red",
            "SELL": "red"
        }
        template_color = color_map.get(analysis.signal, template_color)
        
        # 信号文本
        signal_text_map = {
            "STRONG_BUY": "🔴 强烈买入",
            "BUY": "🟢 买入",
            "HOLD": "🟡 持有",
            "OBSERVE": "👁️ 观察",
            "REDUCE": "⚠️ 减仓",
            "SELL": "🔴 卖出"
        }
        signal_text = signal_text_map.get(analysis.signal, analysis.signal)
        
        # 构建安全边际文本
        if analysis.margin_of_safety is not None:
            if analysis.margin_of_safety > 0:
                mos_text = f"**安全边际: {analysis.margin_of_safety:.1f}%** ✅"
            else:
                mos_text = f"**安全边际: {analysis.margin_of_safety:.1f}%** ❌"
        else:
            mos_text = "安全边际: --"
        
        # 构建目标价上行空间
        upside_text = ""
        if analysis.analyst_target and analysis.current_price > 0:
            upside = (analysis.analyst_target - analysis.current_price) / analysis.current_price * 100
            upside_text = f"\n**分析师目标价**: {analysis.currency}{analysis.analyst_target:.2f} (+{upside:.1f}%)"
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": template_color,
                    "title": {
                        "tag": "plain_text",
                        "content": f"{signal_text} | {analysis.name} ({analysis.code})"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**当前价**\n{analysis.currency}**{analysis.current_price:.2f}**\n⭐ 综合评分: {analysis.total_score}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**PE(TTM)**\n{analysis.pe_ttm:.2f}x\n**Forward PE**\n{analysis.forward_pe:.2f}x" if analysis.forward_pe else f"**PE(TTM)**\n{analysis.pe_ttm:.2f}x"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**PB / PS**\n{analysis.pb:.2f}x / {analysis.ps:.2f}x" if analysis.ps else f"**PB**\n{analysis.pb:.2f}x"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**ROE / 净利率**\n{analysis.roe:.1f}% / {analysis.profit_margin:.1f}%" if analysis.roe and analysis.profit_margin else "--"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**Graham估值**\n{analysis.currency}{analysis.graham_value:.1f}" if analysis.graham_value else "**Graham估值**\n--"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**EPV估值**\n{analysis.currency}{analysis.epv_value:.1f}\n{mos_text}" if analysis.epv_value else f"**EPV估值**\n--\n{mos_text}"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**股息率**: {analysis.dividend_yield:.2f}%{upside_text}"
                        }
                    }
                ]
            }
        }
        
        # 添加风险提示（如果有）
        if analysis.risk_factors:
            risk_text = "\n".join([f"- {r}" for r in analysis.risk_factors[:3]])
            payload["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**⚠️ 风险因素**\n{risk_text}"
                }
            })
        
        # 添加底部时间
        payload["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"---\n*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 价值投资分析系统 v2.0*"
            }
        })
        
        return self._send(payload)
    
    def send_batch_analysis(self, 
                           analyses: List[StockAnalysisResult],
                           report_title: str = "价值投资分析日报") -> Dict:
        """发送批量分析报告（多股票对比卡片）"""
        
        # 分类
        buy_list = [a for a in analyses if a.signal in ["STRONG_BUY", "BUY"]]
        hold_list = [a for a in analyses if a.signal == "HOLD"]
        observe_list = [a for a in analyses if a.signal == "OBSERVE"]
        sell_list = [a for a in analyses if a.signal in ["REDUCE", "SELL"]]
        
        # 构建股票列表文本
        def build_stock_list(stock_list: List[StockAnalysisResult], emoji: str) -> str:
            if not stock_list:
                return ""
            lines = [f"\n{emoji} **{stock_list[0].signal}信号**"]
            for s in sorted(stock_list, key=lambda x: x.total_score, reverse=True):
                mos_text = f"(安全边际{s.margin_of_safety:.0f}%)" if s.margin_of_safety else ""
                lines.append(f"- {s.name}({s.code}): {s.currency}{s.current_price:.2f} | PE{s.pe_ttm:.1f}x | 评分{s.total_score} {mos_text}")
            return "\n".join(lines)
        
        content_parts = []
        content_parts.append(build_stock_list(buy_list, "🟢"))
        content_parts.append(build_stock_list(hold_list, "🟡"))
        content_parts.append(build_stock_list(observe_list, "👁️"))
        content_parts.append(build_stock_list(sell_list, "🔴"))
        
        content = "\n".join([p for p in content_parts if p])
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": "blue",
                    "title": {
                        "tag": "plain_text",
                        "content": f"📊 {report_title} | {datetime.now().strftime('%Y-%m-%d')}"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**共分析 {len(analyses)} 只股票** | 买入机会: {len(buy_list)} | 持有: {len(hold_list)} | 观察: {len(observe_list)} | 卖出: {len(sell_list)}"
                        }
                    },
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
                            "content": f"*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 价值投资分析系统 v2.0*"
                        }
                    }
                ]
            }
        }
        
        return self._send(payload)
    
    def send_alert(self, title: str, content: str, alert_type: str = "warning") -> Dict:
        """发送预警消息
        
        Args:
            title: 预警标题
            content: 预警内容
            alert_type: 预警类型 (warning/error/info/success)
        """
        color_map = {
            "warning": "orange",
            "error": "red",
            "info": "blue",
            "success": "green"
        }
        
        emoji_map = {
            "warning": "⚠️",
            "error": "🚨",
            "info": "ℹ️",
            "success": "✅"
        }
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": color_map.get(alert_type, "blue"),
                    "title": {
                        "tag": "plain_text",
                        "content": f"{emoji_map.get(alert_type, '')} {title}"
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
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"*发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
                        }
                    }
                ]
            }
        }
        
        return self._send(payload)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    import os
    
    # 从logo环境变量读取webhook
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "")
    
    if not webhook_url:
        print("请设置环境变量 FEISHU_WEBHOOK_URL")
        exit(1)
    
    notifier = FeishuNotifier(webhook_url)
    
    # 示例1: 发送简单文本
    # notifier.send_text("测试消息：价值投资分析系统已启动")
    
    # 示例2: 发送单股票分析卡片
    tencent = StockAnalysisResult(
        code="0700.HK",
        name="腾讯控股",
        market="港股",
        current_price=495.20,
        currency="HK$",
        pe_ttm=18.17,
        forward_pe=14.47,
        pb=3.44,
        ps=5.40,
        peg=1.51,
        dividend_yield=1.05,
        roe=18.0,
        profit_margin=29.91,
        graham_value=299.8,
        epv_value=432.0,
        margin_of_safety=15.0,
        total_score=81,
        signal="BUY",
        analyst_target=718.69,
        risk_factors=["游戏监管政策变化", "广告增速放缓", "投资组合减值"]
    )
    
    # notifier.send_stock_analysis_card(tencent)
    
    # 示例3: 发送批量分析报告
    inovance = StockAnalysisResult(
        code="300124.SZ",
        name="汇川技术",
        market="A股",
        current_price=65.34,
        currency="¥",
        pe_ttm=34.85,
        forward_pe=26.53,
        pb=5.27,
        ps=4.17,
        peg=1.14,
        dividend_yield=0.61,
        roe=16.66,
        profit_margin=11.98,
        graham_value=23.2,
        epv_value=34.5,
        margin_of_safety=-89.0,
        total_score=69,
        signal="OBSERVE",
        analyst_target=87.87,
        risk_factors=["制造业下行周期", "新能源渗透率见顶"]
    )
    
    # notifier.send_batch_analysis([tencent, inovance])
    
    # 示例4: 发送预警
    # notifier.send_alert("持仓预警", "汇川技术(300124)价格跌破低位支撑，请关注", "warning")
    
    print("飞书推送模块加载完成")
    print("可用方法:")
    print("  1. notifier.send_text(text)")
    print("  2. notifier.send_markdown(title, content)")
    print("  3. notifier.send_stock_analysis_card(analysis)")
    print("  4. notifier.send_batch_analysis(analyses)")
    print("  5. notifier.send_alert(title, content, alert_type)")
