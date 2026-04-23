#!/usr/bin/env python3
"""测试飞书推送 - 使用示例"""

import sys
sys.path.insert(0, '/Users/alextu/投资助手')

import os
from notifier.feishu_notifier import FeishuNotifier, StockAnalysisResult

# 读取webhook（如果环境变量不存在，需要手动填入）
WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

if not WEBHOOK_URL:
    print("⚠️ 请先设置环境变量 FEISHU_WEBHOOK_URL")
    print("或者直接修改本文件第12行，填入你的webhook地址")
    print("\n获取方法:")
    print("  1. 打开飞书群聊")
    print("  2. 点击群设置 → 智能伙伴 → 添加机器人")
    print("  3. 复制webhook地址")
    exit(1)

# 初始化推送器
notifier = FeishuNotifier(WEBHOOK_URL)

print("🚀 开始测试飞书推送...")
print("-" * 60)

# 准备测试数据 - 腾讯
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
    roa=8.04,
    profit_margin=29.91,
    gross_margin=48.0,
    debt_ratio=40.0,
    graham_value=299.8,
    epv_value=432.0,
    margin_of_safety=15.0,
    total_score=81,
    signal="BUY",
    analyst_target=718.69,
    risk_factors=["游戏监管政策变化", "广告增速放缓", "投资组合减值"],
    opportunity_factors=["监管利空已充分反映", "云业务持续增长"]
)

# 准备测试数据 - 汇川技术
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
    roa=5.25,
    profit_margin=11.98,
    gross_margin=35.0,
    debt_ratio=45.0,
    graham_value=23.2,
    epv_value=34.5,
    margin_of_safety=-89.0,
    total_score=69,
    signal="OBSERVE",
    analyst_target=87.87,
    risk_factors=["制造业下行周期", "新能源渗透率见顶", "竞争加剧"],
    opportunity_factors=["工业自动化赛道优质", "新能源汽车增长"]
)

# 测试1: 发送文本消息
print("\n测试 1/5: 发送文本消息...")
result = notifier.send_text("🚀 价值投资分析系统已启动 | 测试消息")
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}" + 
      (f" - {result.get('error', '')}" if not result['success'] else ""))

# 测试2: 发送Markdown
print("\n测试 2/5: 发送Markdown消息...")
result = notifier.send_markdown(
    "价值投资分析系统 v2.0 测试",
    "**系统状态**: 运行正常\n"
    "**数据源**: Yahoo Finance / AKShare\n"
    "**推送时间**: 每日北京时间18:00\n"
    "---\n"
    "该消息用于测试Markdown格式推送"
)
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

# 测试3: 发送腾讯分析卡片
print("\n测试 3/5: 发送腾讯分析卡片...")
result = notifier.send_stock_analysis_card(tencent)
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

# 测试4: 发送汇川技术分析卡片
print("\n测试 4/5: 发送汇川技术分析卡片...")
result = notifier.send_stock_analysis_card(inovance)
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

# 测试5: 发送批量分析报告
print("\n测试 5/5: 发送批量分析报告...")
result = notifier.send_batch_analysis(
    [tencent, inovance],
    report_title="价值投资分析日报"
)
print(f"  结果: {'✅ 成功' if result['success'] else '❌ 失败'}")

print("\n" + "=" * 60)
print("测试完成! 请检查飞书消息是否收到")
print("=" * 60)
