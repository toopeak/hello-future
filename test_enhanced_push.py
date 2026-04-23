#!/usr/bin/env python3
"""测试增强版飞书推送 - 多维度价值分析
"""

import sys
sys.path.insert(0, '/Users/alextu/投资助手')

import os
from notifier.enhanced_feishu_notifier import (
    EnhancedFeishuNotifier, 
    EnhancedStockAnalysis,
    HistoricalValuation,
    IndustryComparison,
    QualityBreakdown
)

WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

if not WEBHOOK_URL:
    print("⚠️ 请设置环境变量 FEISHU_WEBHOOK_URL")
    print("或修改本文件第12行填入webhook地址")
    exit(1)

notifier = EnhancedFeishuNotifier(WEBHOOK_URL)

print("🚀 测试增强版飞书推送（多维度价值分析）...")
print("-" * 60)

# 构建腾讯增强版分析数据
tencent = EnhancedStockAnalysis(
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
    ev_ebitda=11.06,
    dividend_yield=1.05,
    roe=18.0,
    roa=8.04,
    profit_margin=29.91,
    gross_margin=48.0,
    operating_margin=33.13,
    debt_ratio=40.0,
    current_ratio=1.5,
    interest_coverage=15.0,
    revenue_growth_3y=12.5,
    profit_growth_3y=15.2,
    fcf_growth_3y=8.5,
    operating_cash_flow=1800.0,
    free_cash_flow=1200.0,
    fcf_yield=2.68,
    graham_value=299.8,
    epv_value=432.0,
    dcf_value=580.0,
    margin_of_safety=15.0,
    historical=HistoricalValuation(
        pe_min=12.0,
        pe_max=45.0,
        pe_median=22.0,
        pe_avg=24.5,
        pe_percentile=30.0,
        pb_min=2.5,
        pb_max=8.0,
        pb_median=4.0,
        pb_avg=4.2,
        pb_percentile=25.0
    ),
    industry=IndustryComparison(
        industry_name="互联网信息",
        industry_avg_pe=25.0,
        industry_avg_pb=4.5,
        industry_avg_roe=12.0,
        pe_premium=-27.3,
        pb_premium=-23.6,
        roe_premium=50.0,
        ranking_in_industry=2,
        total_in_industry=50
    ),
    quality=QualityBreakdown(
        profitability_score=95,
        growth_score=80,
        financial_health_score=85,
        stability_score=88,
        management_score=90,
        moat_score=85
    ),
    total_score=81,
    signal="BUY",
    analyst_target=718.69,
    upside=45.1,
    risk_factors=["游戏监管政策变化", "广告增速放缓", "投资组合减值"],
    opportunity_factors=["监管利空已充分反映", "云业务持续增长", "游戏业务复苏"]
)

# 构建汇川技术增强版分析数据
inovance = EnhancedStockAnalysis(
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
    ev_ebitda=31.67,
    dividend_yield=0.61,
    roe=16.66,
    roa=5.25,
    profit_margin=11.98,
    gross_margin=35.0,
    operating_margin=13.06,
    debt_ratio=45.0,
    current_ratio=1.8,
    interest_coverage=8.0,
    revenue_growth_3y=35.0,
    profit_growth_3y=25.0,
    fcf_growth_3y=20.0,
    operating_cash_flow=35.0,
    free_cash_flow=25.0,
    fcf_yield=1.42,
    graham_value=23.2,
    epv_value=34.5,
    dcf_value=45.0,
    margin_of_safety=-89.0,
    historical=HistoricalValuation(
        pe_min=20.0,
        pe_max=65.0,
        pe_median=38.0,
        pe_avg=40.0,
        pe_percentile=40.0,
        pb_min=3.5,
        pb_max=9.0,
        pb_median=6.0,
        pb_avg=6.2,
        pb_percentile=35.0
    ),
    industry=IndustryComparison(
        industry_name="工业自动化",
        industry_avg_pe=32.0,
        industry_avg_pb=5.0,
        industry_avg_roe=14.0,
        pe_premium=8.9,
        pb_premium=5.4,
        roe_premium=19.0,
        ranking_in_industry=5,
        total_in_industry=80
    ),
    quality=QualityBreakdown(
        profitability_score=75,
        growth_score=90,
        financial_health_score=75,
        stability_score=70,
        management_score=80,
        moat_score=75
    ),
    total_score=69,
    signal="OBSERVE",
    analyst_target=87.87,
    upside=34.5,
    risk_factors=["制造业下行周期", "新能源渗透率见顶", "竞争加剧"],
    opportunity_factors=["工业自动化赛道优质", "新能源汽车增长", "国产替代加速"]
)

# 测试：发送腾讯增强版分析卡片
print("\n测试 1/3: 发送腾讯增强版分析卡片...")
print("  包含: 基础估值 + 财务质量 + 成长性 + 历史PE + 行业对比 + 质量细分 + 风险/机会")
result = notifier.send_enhanced_analysis_card(tencent)
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

# 测试：发送汇川技术增强版分析卡片
print("\n测试 2/3: 发送汇川技术增强版分析卡片...")
result = notifier.send_enhanced_analysis_card(inovance)
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

# 测试：发送多维度对比报告
print("\n测试 3/3: 发送多维度对比报告...")
result = notifier.send_multi_dimension_report([tencent, inovance])
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

print("\n" + "=" * 60)
print("测试完成! 请检查飞书消息，对比两版本差异")
print("=" * 60)
