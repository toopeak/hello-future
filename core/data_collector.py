"""
数据采集模块 - 价值投资分析系统
数据源: AKShare(A股) + yfinance(港股/美股)
作者: Faria
"""

import os
import sys
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 缓存目录
CACHE_DIR = Path("/Users/alextu/投资助手/cache")
CACHE_DIR.mkdir(exist_ok=True)


@dataclass
class FinancialData:
    """财务数据"""
    code: str
    name: str = ""
    market: str = ""  # A股/港股/美股
    
    # 基础行情
    current_price: float = 0.0
    currency: str = ""
    market_cap: float = 0.0  # 市值（亿）
    
    # 估值指标
    pe_ttm: Optional[float] = None
    forward_pe: Optional[float] = None
    pb: Optional[float] = None
    ps: Optional[float] = None
    peg: Optional[float] = None
    dividend_yield: Optional[float] = None
    
    # 盈利能力
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    
    # 财务健康
    debt_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # 现金流
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    
    # 成长性
    revenue_growth_3y: Optional[float] = None
    profit_growth_3y: Optional[float] = None
    
    # 历史估值
    pe_min_5y: Optional[float] = None
    pe_max_5y: Optional[float] = None
    pe_median_5y: Optional[float] = None
    pe_percentile: Optional[float] = None
    
    # 时间戳
    update_time: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DataCollector:
    """数据采集器"""
    
    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl  # 缓存有效期(秒)
        
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        return CACHE_DIR / f"{key}_{datetime.now().strftime('%Y%m%d')}.json"
    
    def _load_cache(self, key: str) -> Optional[Dict]:
        """加载缓存"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期
                    cache_time = datetime.fromisoformat(data.get('_cache_time', '2000-01-01'))
                    if (datetime.now() - cache_time).seconds < self.cache_ttl:
                        logger.info(f"使用缓存: {key}")
                        return data.get('data')
            except Exception as e:
                logger.warning(f"读取缓存失败: {e}")
        return None
    
    def _save_cache(self, key: str, data: Dict):
        """保存缓存"""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    '_cache_time': datetime.now().isoformat(),
                    'data': data
                }, f, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def get_a_stock_data(self, code: str) -> FinancialData:
        """
        获取A股数据
        
        Args:
            code: 股票代码，如 "300124"
        """
        logger.info(f"获取A股数据: {code}")
        
        cache_key = f"a_stock_{code}"
        cached = self._load_cache(cache_key)
        if cached:
            return FinancialData(**cached)
        
        result = FinancialData(code=code, market="A股", currency="¥")
        
        try:
            import akshare as ak
            
            # 1. 获取实时行情
            try:
                df_spot = ak.stock_zh_a_spot_em()
                stock_row = df_spot[df_spot['代码'] == code]
                if not stock_row.empty:
                    row = stock_row.iloc[0]
                    result.name = str(row.get('名称', ''))
                    result.current_price = self._safe_float(row.get('最新价'))
                    result.pe_ttm = self._safe_float(row.get('市盈率-动态'))
                    result.pb = self._safe_float(row.get('市净率'))
                    result.ps = self._safe_float(row.get('市销率'))
                    result.market_cap = self._safe_float(row.get('总市值'))
            except Exception as e:
                logger.warning(f"获取{code}实时行情失败: {e}")
            
            # 2. 获取财务摘要
            try:
                df_fin = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
                if not df_fin.empty:
                    latest = df_fin.iloc[0]
                    result.roe = self._safe_float(latest.get('净资产收益率'))
                    result.roa = self._safe_float(latest.get('总资产报酬率'))
                    result.gross_margin = self._safe_float(latest.get('毛利率'))
                    result.net_margin = self._safe_float(latest.get('净利率'))
                    result.operating_margin = self._safe_float(latest.get('销售净利率'))
                    result.debt_ratio = self._safe_float(latest.get('资产负债率'))
                    result.current_ratio = self._safe_float(latest.get('流动比率'))
                    result.revenue_growth_3y = self._safe_float(latest.get('营业总收入同比增长率'))
                    result.profit_growth_3y = self._safe_float(latest.get('净利润同比增长率'))
            except Exception as e:
                logger.warning(f"获取{code}财务数据失败: {e}")
            
            # 3. 获取历史PE
            try:
                hist_pe = self._get_a_stock_pe_history(code)
                if hist_pe:
                    result.pe_min_5y = hist_pe['min']
                    result.pe_max_5y = hist_pe['max']
                    result.pe_median_5y = hist_pe['median']
                    result.pe_percentile = hist_pe['percentile']
            except Exception as e:
                logger.warning(f"获取{code}历史PE失败: {e}")
            
        except ImportError:
            logger.error("未安装akshare，请运行: pip3 install akshare")
        except Exception as e:
            logger.error(f"获取{code}数据失败: {e}")
        
        result.update_time = datetime.now().isoformat()
        self._save_cache(cache_key, result.to_dict())
        return result
    
    def get_hk_stock_data(self, code: str) -> FinancialData:
        """
        获取港股数据
        
        Args:
            code: 股票代码，如 "0700.HK"
        """
        logger.info(f"获取港股数据: {code}")
        
        cache_key = f"hk_stock_{code.replace('.', '_')}"
        cached = self._load_cache(cache_key)
        if cached:
            return FinancialData(**cached)
        
        result = FinancialData(code=code, market="港股", currency="HK$")
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(code)
            info = ticker.info
            
            result.name = info.get('longName', '') or info.get('shortName', '')
            result.current_price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
            result.market_cap = (info.get('marketCap', 0) or 0) / 1e8  # 转换为亿
            result.pe_ttm = info.get('trailingPE')
            result.forward_pe = info.get('forwardPE')
            result.pb = info.get('priceToBook')
            result.ps = info.get('priceToSalesTrailing12Months')
            result.peg = info.get('pegRatio')
            result.dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else None
            
            result.roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None
            result.roa = info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else None
            result.gross_margin = info.get('grossMargins', 0) * 100 if info.get('grossMargins') else None
            result.net_margin = info.get('profitMargins', 0) * 100 if info.get('profitMargins') else None
            result.operating_margin = info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else None
            result.debt_ratio = info.get('debtToEquity', 0)
            result.current_ratio = info.get('currentRatio')
            
            # 历史PE
            try:
                hist = ticker.history(period="5y")
                if not hist.empty:
                    # 简化处理：用价格区间估算
                    result.pe_min_5y = result.pe_ttm * (hist['Close'].min() / result.current_price) if result.current_price > 0 else None
                    result.pe_max_5y = result.pe_ttm * (hist['Close'].max() / result.current_price) if result.current_price > 0 else None
                    result.pe_median_5y = result.pe_ttm * (hist['Close'].median() / result.current_price) if result.current_price > 0 else None
            except Exception as e:
                logger.warning(f"获取{code}历史数据失败: {e}")
            
        except ImportError:
            logger.error("未安装yfinance，请运行: pip3 install yfinance")
        except Exception as e:
            logger.error(f"获取{code}数据失败: {e}")
        
        result.update_time = datetime.now().isoformat()
        self._save_cache(cache_key, result.to_dict())
        return result
    
    def _get_a_stock_pe_history(self, code: str) -> Optional[Dict]:
        """获取A股历史PE数据"""
        try:
            import akshare as ak
            
            # 确定symbol
            if code.startswith('6'):
                symbol = f"sh{code}"
            elif code.startswith('0') or code.startswith('3'):
                symbol = f"sz{code}"
            else:
                symbol = code
            
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d')
            end_date = datetime.now().strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                   start_date=start_date, end_date=end_date)
            
            if '市盈率' in df.columns:
                pe_list = df['市盈率'].dropna()
                pe_list = pe_list[pe_list > 0]
                if len(pe_list) > 0:
                    return {
                        'min': float(pe_list.min()),
                        'max': float(pe_list.max()),
                        'median': float(pe_list.median()),
                        'mean': float(pe_list.mean()),
                        'percentile': None  # 需要当前PE计算
                    }
        except Exception as e:
            logger.warning(f"获取历史PE失败: {e}")
        return None
    
    def get_risk_free_rate(self) -> float:
        """获取无风险利率（10年期国债收益率）"""
        try:
            import akshare as ak
            df = ak.bond_china_yield(start_date=datetime.now().strftime('%Y%m%d'),
                                    end_date=datetime.now().strftime('%Y%m%d'))
            if not df.empty and '10年期国债收益率' in df.columns:
                rate = float(df['10年期国债收益率'].iloc[0])
                return rate / 100
        except Exception as e:
            logger.warning(f"获取国债收益率失败: {e}")
        return 0.025  # 默认2.5%
    
    @staticmethod
    def _safe_float(val, default: Optional[float] = None) -> Optional[float]:
        """安全转换为浮点数"""
        if val is None or val == '--' or val == 'None' or val == '-':
            return default
        try:
            s = str(val).replace('%', '').replace('亿', '').replace(',', '').replace('HK$', '').replace('¥', '')
            return float(s)
        except (ValueError, TypeError):
            return default


# ==================== 测试 ====================
if __name__ == "__main__":
    collector = DataCollector()
    
    print("测试获取汇川技术(300124)...")
    hc = collector.get_a_stock_data("300124")
    print(f"  名称: {hc.name}")
    print(f"  价格: ¥{hc.current_price}")
    print(f"  PE: {hc.pe_ttm}")
    print(f"  ROE: {hc.roe}%")
    print(f"  净利率: {hc.net_margin}%")
    
    print("\n测试获取腾讯(0700.HK)...")
    tx = collector.get_hk_stock_data("0700.HK")
    print(f"  名称: {tx.name}")
    print(f"  价格: HK${tx.current_price}")
    print(f"  PE: {tx.pe_ttm}")
    print(f"  ROE: {tx.roe}%")
    print(f"  净利率: {tx.net_margin}%")
