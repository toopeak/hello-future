#!/usr/bin/env python3
"""
Buffett-Munger 价值投资分析
核心: 护城河 + ROE + 现金流 + 安全边际 + 能力圈
作者: Faria
"""

import sys
sys.path.insert(0, '/Users/alextu/投资助手')

import os
import requests
from datetime import datetime

WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
if not WEBHOOK_URL:
    print("请设置 FEISHU_WEBHOOK_URL")
    exit(1)


def send_buffett_report():
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": "🏷️ Buffett-Munger 价值投资分析"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "*“价格是你付出的，价值是你得到的。”* \u2014\u2014 Warren Buffett\n"
                                "*“以合理的价格买下优秀的企业，远好于以便宜的价格买下普通的企业。”* \u2014\u2014 Charlie Munger"
                    }
                },
                {"tag": "hr"},

                # ==================== 腾讯 ====================
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "## 🎯 腾讯控股 (0700.HK) \u2014 待定价格的优秀企业"
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": "**当前价格**
HK$495.20
**综合评级**: 持有/轻仓买入"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": "**安全边际**
15-20%
**核心**: Forward PE 14x"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 一、Buffett看护城河（Moat）\n"
                                "✅ **微信生态**: 日活12亿用户，网络效应极强 — “据此我可以睡好觉”\n"
                                "✅ **游戏IP**: 《王者荣耀》《和平精英》等顶级IP，用户粘性高\n"
                                "⚠️ **政策风险**: 游戏版号审批、青少年保护政策削弱了护城河确定性\n"
                                "⚠️ **投资组合**: 持有上市公司股权价值波动大，这部分难以估值"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 二、Buffett看财务数据（五年均值）\n"
                                "| 指标 | 数据 | Buffett标准 | 评价 |\n"
                                "|------|------|----------|------|\n"
                                "| ROE | ~18% | >15% | ✅ 优秀 |\n"
                                "| 净利率 | 30% | >10% | ✅ 极佳 |\n"
                                "| 毛利率 | 48% | >40% | ✅ 很好 |\n"
                                "| 负债率 | 40% | <60% | ✅ 健康 |\n"
                                "| FCF/Net Income | >100% | >80% | ✅ 现金流极佳 |\n"
                                "| 市盈率 | 18x | <20x | ✅ 合理 |"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 三、Munger看质量（与伟大企业共成长）\n"
                                "✅ **管理层**: 刘点森团队稳健，投资记录优秀\n"
                                "✅ **复利能力**: 微信生态的网络效应具有自然增长动力\n"
                                "⚠️ **能力圈**: 投资组合跨越了能力圈，普通投资者难以理解其价值\n"
                                "✅ **长期持有**: 如果政策稳定，是值得长期持有的企业"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 四、核心结论\n"
                                "**Buffett会说**: *"这是一家优秀的企业，护城河很宽，但政策风险让护城河的确定性打了折扣。Forward PE 14x提供了一定的安全边际，但不是极大的。我会小仓位持有，等待更大的折扣。"*\n\n"
                                "**Munger会说**: *"以合理的价格买下这家企业是可以的，但不是“强烈买入”的机会。如果能回券到450港元以下（PE 16x），那将是一个更好的入场点。"*\n\n"
                                "💡 **操作建议**: 当前价可建仓30%仓位，450港元加仓30%，400港元满仓。"
                    }
                },

                {"tag": "hr"},

                # ==================== 汇川技术 ====================
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "## 🎯 汇川技术 (300124.SZ) \u2014 好企业，但价格不友好"
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": "**当前价格**
¥65.34
**综合评级**: 观察/等待"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": "**安全边际**
无
**核心**: PE 35x 太贵"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 一、Buffett看护城河（Moat）\n"
                                "✅ **国产龙头**: 国内工控领域第一，品牌认知度高\n"
                                "✅ **规模效应**: 服务网络覆盖全国，成本优势明显\n"
                                "⚠️ **技术更替**: 工控行业技术迭代快，今天的领先不保证明天\n"
                                "❌ **国际竞争**: 西门子、ABB等国际巨头仍占据高端市场"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 二、Buffett看财务数据（五年均值）\n"
                                "| 指标 | 数据 | Buffett标准 | 评价 |\n"
                                "|------|------|----------|------|\n"
                                "| ROE | 16.7% | >15% | ✅ 良好 |\n"
                                "| 净利率 | 12% | >10% | ✅ 合格 |\n"
                                "| 毛利率 | 35% | >40% | ⚠️ 偏低 |\n"
                                "| 负债率 | 45% | <60% | ✅ 健康 |\n"
                                "| FCF/Net Income | ~70% | >80% | ⚠️ 资本开支大 |\n"
                                "| 市盈率 | 35x | <20x | ❌ 太贵 |"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 三、Munger看质量（与伟大企业共成长）\n"
                                "✅ **行业赛道**: 工业自动化+新能源汽车，长期好赛道\n"
                                "⚠️ **复利能力**: 资本开支大，需不断投入研发和产能，自由现金流弱\n"
                                "❌ **能力圈**: 工控行业技术变化快，普通投资者很难跟上\n"
                                "❌ **价格**: PE 35x意味着已经提前反映了未来3-5年的增长"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 四、核心结论\n"
                                "**Buffett会说**: *"这家公司不错，ROE达标，财务健康。但是——我从不代35倍市盈率买任何东西。每股盈利与市场价格之间的关系已经失调。等待吧。"*\n\n"
                                "**Munger会说**: *"我们寻找的是‘以公平价格买入的伟大企业’，而不是‘以高价买入的好企业’。这家公司是后者。安全边际为负数，没有安全垫。"*\n\n"
                                "💡 **操作建议**: 等待回调至¥45-50元（PE 25x）再考虑建仓。现在买入，你付出的是价格，得到的不是价值。"
                    }
                },

                {"tag": "hr"},

                # ==================== 对比总结 ====================
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "## 📊 Buffett-Munger 两家对比"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "| 维度 | 腾讯 0700.HK | 汇川技术 300124.SZ | Buffett偏好 |\n"
                                "|------|--------------|-------------------|----------|\n"
                                "| 护城河确定性 | 强（微信） | 中（品牌+规模） | ✅ 腾讯 |\n"
                                "| ROE | ~18% | 16.7% | ✅ 腾讯 |\n"
                                "| 净利率 | 30% | 12% | ✅ 腾讯 |\n"
                                "| 现金流质量 | 极佳 | 一般 | ✅ 腾讯 |\n"
                                "| 安全边际 | 15-20% | 无 | ✅ 腾讯 |\n"
                                "| PE | 18x | 35x | ✅ 腾讯 |\n"
                                "| 成长性 | 稳健 | 高速 | 平手 |\n"
                                "| 能力圈 | 复杂 | 复杂 | 均难 |\n"
                                "| 当前操作 | 轻仓买入 | 观察等待 | - |\n"
                    }
                },

                {"tag": "hr"},

                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "### 核心记忆卡片\n"
                                "👇 *"我们的策略是专注于找出拥有持续竞争优势、由能干的管理层管理、以合理价格出售的企业。"*\n"
                                "\u2014\u2014 Warren Buffett\n\n"
                                "👇 *"如果你真的想要在生活中取得成功，那就去做你熟悉的事情。"*\n"
                                "\u2014\u2014 Charlie Munger"
                    }
                },

                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"---\n*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 框架: Buffett-Munger 价值投资 | 核心指标: 护城河/ROE/现金流/安全边际*"
                    }
                }
            ]
        }
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    result = response.json()

    if result.get("code") == 0:
        print("✅ 推送成功！请查收飞书消息")
    else:
        print(f"❌ 推送失败: {result}")


if __name__ == "__main__":
    send_buffett_report()
