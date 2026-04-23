#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资助手 - 股票数据获取脚本
用 yfinance 获取价格 + 基本面数据，输出 JSON
"""

import sys
import json
import yfinance as yf

def get_stock_data(code):
    """获取单只股票的完整数据"""
    try:
        stock = yf.Ticker(code)
        info = stock.info
        
        # 价格数据（从 info 里取最新）
        price_data = {
            "code": code,
            "name": info.get("shortName") or info.get("longName") or code,
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "prev_close": info.get("previousClose"),
            "open": info.get("open"),
            "high": info.get("dayHigh"),
            "low": info.get("dayLow"),
            "volume": info.get("volume"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        }
        
        # 基本面数据
        fundamentals = {
            "pe": info.get("trailingPE"),                    # 市盈率
            "forward_pe": info.get("forwardPE"),             # 远期市盈率
            "pb": info.get("priceToBook"),                   # 市净率
            "roe": info.get("returnOnEquity"),               # 净资产收益率
            "roa": info.get("returnOnAssets"),               # 总资产收益率
            "gross_margin": info.get("grossMargins"),        # 毛利率
            "profit_margin": info.get("profitMargins"),      # 净利率
            "revenue_growth": info.get("revenueGrowth"),     # 营收增长率
            "earnings_growth": info.get("earningsGrowth"),   # 盈利增长率
            "debt_to_equity": info.get("debtToEquity"),      # 负债权益比
            "current_ratio": info.get("currentRatio"),       # 流动比率
            "dividend_yield": info.get("dividendYield"),     # 股息率
            "free_cashflow": info.get("freeCashflow"),       # 自由现金流
            "market_cap": info.get("marketCap"),             # 市值
            "sector": info.get("sector"),                    # 行业
            "industry": info.get("industry"),                # 细分行业
        }
        
        # 计算涨跌幅
        if price_data["price"] and price_data["prev_close"]:
            change = price_data["price"] - price_data["prev_close"]
            change_pct = (change / price_data["prev_close"]) * 100
            price_data["change"] = round(change, 2)
            price_data["change_pct"] = round(change_pct, 2)
        else:
            price_data["change"] = 0
            price_data["change_pct"] = 0
        
        return {
            "success": True,
            "price": price_data,
            "fundamentals": fundamentals
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "code": code
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "请提供股票代码"}, ensure_ascii=False))
        sys.exit(1)
    
    code = sys.argv[1]
    result = get_stock_data(code)
    print(json.dumps(result, ensure_ascii=False, indent=2))
