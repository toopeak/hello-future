#!/usr/bin/env python3
"""
价值投资分析系统 - 主控程序
支持: A股 + 港股 自动分析 + 飞书推送
框架: Buffett-Munger 价值投资
作者: Faria
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入核心模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.data_collector import DataCollector, FinancialData
from core.valuation_engine import ValuationEngine
from core.decision_engine import DecisionEngine, FinalAnalysis
from notifier.feishu_notifier import FeishuNotifier

# 配置
CONFIG = {
    'cache_ttl': 3600,
    'default_risk_free_rate': 0.025,
    'stock_pool': []
}


def load_config() -> Dict:
    """加载配置"""
    config_path = Path(__file__).parent / 'config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
    
    # 默认配置
    return {
        'stock_pool': [
            {'code': '300124', 'market': 'A股', 'name': '汇川技术'},
            {'code': '600519', 'market': 'A股', 'name': '贵州茅台'},
            {'code': '000858', 'market': 'A股', 'name': '五粮液'},
            {'code': '0700.HK', 'market': '港股', 'name': '腾讯控股'},
            {'code': '3690.HK', 'market': '港股', 'name': '美团-W'},
            {'code': '2318.HK', 'market': '港股', 'name': '中国平安'},
        ],
        'watchlist': [
            {'code': '300750', 'market': 'A股', 'name': '宁德时代'},
            {'code': '601318', 'market': 'A股', 'name': '中国平安'},
            {'code': '0981.HK', 'market': '港股', 'name': '中芯国际'},
        ]
    }


def analyze_stock(code: str, market: str, name: str = "",
                  collector: DataCollector = None,
                  valuation_engine: ValuationEngine = None,
                  decision_engine: DecisionEngine = None) -> FinalAnalysis:
    """
    分析单只股票
    """
    logger.info(f"开始分析 {code} ({market})...")
    
    # 采集数据
    if market == 'A股':
        data = collector.get_a_stock_data(code)
    else:
        data = collector.get_hk_stock_data(code)
    
    if name and not data.name:
        data.name = name
    
    # 估值
    valuation = valuation_engine.evaluate(data)
    
    # 决策
    analysis = decision_engine.analyze(data, valuation)
    
    logger.info(f"  分析完成: {data.name} | 评分:{analysis.total_score} | 信号:{analysis.signal}")
    
    return analysis


def format_push_message(analysis: FinalAnalysis) -> str:
    """格式化推送消息"""
    signal_emoji = {
        'STRONG_BUY': '🔴',
        'BUY': '🟢',
        'HOLD': '🟡',
        'OBSERVE': '👁️',
        'REDUCE': '⚠️',
        'SELL': '🔴'
    }
    
    emoji = signal_emoji.get(analysis.signal, '➖')
    
    # Buffett结论
    buffett_opinion = ""
    if analysis.buffett.moat_score >= 80:
        buffett_opinion = "护城河深厚"
    elif analysis.buffett.moat_score >= 60:
        buffett_opinion = "护城河一般"
    else:
        buffett_opinion = "护城河弱"
    
    # Munger结论
    munger_opinion = ""
    if analysis.valuation.margin_of_safety and analysis.valuation.margin_of_safety > 15:
        munger_opinion = "价格合理"
    elif analysis.valuation.margin_of_safety and analysis.valuation.margin_of_safety > 0:
        munger_opinion = "价格公平"
    else:
        munger_opinion = "价格偏贵"
    
    msg = f"""
{emoji} **{analysis.name} ({analysis.code})** - {analysis.signal}
**当前价**: {analysis.currency}{analysis.current_price:.2f} | **评分**: {analysis.total_score}
**安全边际**: {analysis.valuation.margin_of_safety:.1f}% | **PE**: {analysis.valuation.current_price / (analysis.valuation.current_price / analysis.valuation.graham_value * 2.5) if analysis.valuation.graham_value else 0:.1f}x
**护城河**: {buffett_opinion}({analysis.buffett.moat_score}) | **财务**: {analysis.buffett.financial_score}
**操作**: {analysis.recommendation}
"""
    return msg


def run_analysis(push: bool = True, stock_pool: List[Dict] = None) -> List[FinalAnalysis]:
    """
    运行完整分析
    
    Args:
        push: 是否推送到飞书
        stock_pool: 自定义股票池，为None则使用配置文件中的股票池
    """
    logger.info("=" * 60)
    logger.info("价值投资分析系统启动")
    logger.info("=" * 60)
    
    # 加载配置
    config = load_config()
    if stock_pool is None:
        stock_pool = config.get('stock_pool', [])
    
    if not stock_pool:
        logger.error("股票池为空，请配置config.json")
        return []
    
    # 初始化引擎
    collector = DataCollector(cache_ttl=CONFIG['cache_ttl'])
    risk_free_rate = collector.get_risk_free_rate()
    logger.info(f"无风险利率: {risk_free_rate*100:.2f}%")
    
    valuation_engine = ValuationEngine(risk_free_rate=risk_free_rate)
    decision_engine = DecisionEngine()
    
    # 分析每只股票
    results = []
    for stock in stock_pool:
        try:
            analysis = analyze_stock(
                code=stock['code'],
                market=stock['market'],
                name=stock.get('name', ''),
                collector=collector,
                valuation_engine=valuation_engine,
                decision_engine=decision_engine
            )
            results.append(analysis)
        except Exception as e:
            logger.error(f"分析 {stock['code']} 失败: {e}")
            continue
    
    # 排序
    results.sort(key=lambda x: x.total_score, reverse=True)
    
    # 打印报告
    logger.info("\n" + "=" * 60)
    logger.info("分析报告汇总")
    logger.info("=" * 60)
    for r in results:
        logger.info(f"{r.name:12s} | 评分:{r.total_score:3d} | 信号:{r.signal:10s} | "
                   f"安全边际:{r.valuation.margin_of_safety or 0:+.1f}%")
    
    # 推送到飞书
    if push:
        webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("未设置FEISHU_WEBHOOK_URL，跳过推送")
        else:
            logger.info("\n开始推送到飞书...")
            notifier = FeishuNotifier(webhook_url)
            
            # 发送批量报告
            buy_signals = [r for r in results if r.signal in ['STRONG_BUY', 'BUY']]
            observe_signals = [r for r in results if r.signal == 'OBSERVE']
            sell_signals = [r for r in results if r.signal in ['REDUCE', 'SELL']]
            
            # 构建详细消息
            content_parts = []
            content_parts.append(f"**价值投资日报 | {datetime.now().strftime('%Y-%m-%d')}**")
            content_parts.append(f"共分析 {len(results)} 只 | 买入:{len(buy_signals)} | 观察:{len(observe_signals)} | 卖出:{len(sell_signals)}\n")
            
            # 每只股票详细分析
            for r in results[:5]:  # 最多5只
                emoji = signal_emoji.get(r.signal, '➖')
                content_parts.append(f"\n---\n")
                content_parts.append(f"{emoji} **{r.name} ({r.code})** | {r.signal} | 评分:{r.total_score}")
                content_parts.append(f"**当前价**: {r.currency}{r.current_price:.2f} | **安全边际**: {r.valuation.margin_of_safety or 0:+.1f}%")
                
                # Buffett护城河
                content_parts.append(f"**护城河**: {r.buffett.moat_assessment}")
                
                # 核心财务数据
                fin_lines = []
                if r.buffett.financial_score:
                    fin_lines.append(f"ROE:{r.buffett.financial_score} 财务健康:{r.buffett.financial_score}")
                if r.valuation.graham_value:
                    fin_lines.append(f"Graham估值:{r.currency}{r.valuation.graham_value:.1f}")
                if r.valuation.epv_value:
                    fin_lines.append(f"EPV:{r.currency}{r.valuation.epv_value:.1f}")
                if fin_lines:
                    content_parts.append(" | ".join(fin_lines))
                
                # 专家观点
                content_parts.append(f"**Buffett**: {r.buffett.verdict or '护城河' + str(r.buffett.moat_score) + '分'}")
                content_parts.append(f"**Munger**: {r.munger.verdict or r.munger.business_quality}")
                
                # 操作建议
                content_parts.append(f"💡 **建议**: {r.recommendation}")
                
                # 风险/机会
                if r.risk_factors:
                    content_parts.append(f"⚠️ 风险: {', '.join(r.risk_factors[:2])}")
                if r.opportunity_factors:
                    content_parts.append(f"✅ 机会: {', '.join(r.opportunity_factors[:2])}")
            
            # 底部说明
            content_parts.append(f"\n---\n*框架: Buffett-Munger | 数据源: Yahoo Finance/AKShare*")
            
            # 发送
            notifier.send_markdown("价值投资分析日报", "\n".join(content_parts))
            logger.info("推送完成")
    
    # 保存报告
    save_report(results)
    
    return results


def save_report(results: List[FinalAnalysis], output_dir: str = "reports"):
    """保存分析报告"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    report_data = []
    for r in results:
        report_data.append({
            'code': r.code,
            'name': r.name,
            'market': r.market,
            'price': r.current_price,
            'currency': r.currency,
            'signal': r.signal,
            'total_score': r.total_score,
            'margin_of_safety': r.valuation.margin_of_safety,
            'graham_value': r.valuation.graham_value,
            'epv_value': r.valuation.epv_value,
            'dcf_value': r.valuation.dcf_value,
            'fair_value_mid': r.valuation.fair_value_mid,
            'moat_score': r.buffett.moat_score,
            'financial_score': r.buffett.financial_score,
            'confidence': r.confidence,
            'recommendation': r.recommendation,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    
    import pandas as pd
    df = pd.DataFrame(report_data)
    filename = output_path / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    logger.info(f"报告已保存至 {filename}")


def main():
    parser = argparse.ArgumentParser(description='价值投资分析系统')
    parser.add_argument('--no-push', action='store_true', help='不推送到飞书')
    parser.add_argument('--stocks', nargs='+', help='指定分析的股票，格式: 代码:市场')
    args = parser.parse_args()
    
    # 构建股票池
    stock_pool = None
    if args.stocks:
        stock_pool = []
        for s in args.stocks:
            parts = s.split(':')
            if len(parts) == 2:
                stock_pool.append({'code': parts[0], 'market': parts[1]})
            else:
                # 默认A股
                stock_pool.append({'code': s, 'market': 'A股'})
    
    # 运行分析
    results = run_analysis(
        push=not args.no_push,
        stock_pool=stock_pool
    )
    
    logger.info("\n分析完成!")
    return results


if __name__ == '__main__':
    main()
