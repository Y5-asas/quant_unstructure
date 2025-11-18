"""
基于 yfinance 的实时股票数据源实现
"""
import pandas as pd
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime
from backend.core.data_source import StockDataSource
from backend.core.models import RealtimeStockData


class YahooFinanceDataSource(StockDataSource):
    """使用 yfinance 从 Yahoo Finance 获取股票数据"""
    
    def __init__(self, delay: float = 0.5):
        """
        Args:
            delay: 每次请求之间的延迟（秒），避免请求过快
        """
        self.delay = delay
    
    def get_realtime_data(self, symbols: List[str]) -> Dict[str, RealtimeStockData]:
        """
        获取实时股票数据
        
        Args:
            symbols: 股票代码列表，如 ["AAPL", "MSFT"]
            
        Returns:
            股票代码到实时数据的映射
        """
        import time
        
        result = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                quote = ticker.history(period="1d", interval="1m")
                
                if not quote.empty:
                    latest = quote.iloc[-1]
                    result[symbol] = RealtimeStockData(
                        symbol=symbol,
                        price=float(latest["Close"]),
                        open_price=float(quote.iloc[0]["Open"]),
                        high=float(quote["High"].max()),
                        low=float(quote["Low"].min()),
                        volume=int(quote["Volume"].sum()),
                        timestamp=datetime.now(),
                    )
                else:
                    # 如果没有实时数据，尝试获取最新交易日的数据
                    hist = ticker.history(period="5d")
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        result[symbol] = RealtimeStockData(
                            symbol=symbol,
                            price=float(latest["Close"]),
                            open_price=float(latest["Open"]),
                            high=float(latest["High"]),
                            low=float(latest["Low"]),
                            volume=int(latest["Volume"]),
                            timestamp=datetime.now(),
                        )
                
                time.sleep(self.delay)  # 避免请求过快
                
            except Exception as e:
                print(f"获取 {symbol} 实时数据失败: {e}")
                continue
        
        return result
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取历史股票数据
        
        Args:
            symbol: 股票代码，如 "AAPL"
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"
            
        Returns:
            包含日期、开盘、收盘等信息的 DataFrame
        """
        # 使用相对导入避免循环依赖
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
        from utils.fetch_dow30_data import fetch_single_stock_data
        
        df = fetch_single_stock_data(symbol, start_date=start_date, end_date=end_date)
        return df
    
    def subscribe_updates(self, symbols: List[str], callback: callable):
        """
        订阅实时更新（使用轮询方式）
        
        Args:
            symbols: 股票代码列表
            callback: 数据更新回调函数
        """
        import time
        import threading
        
        def polling_loop():
            while True:
                try:
                    data = self.get_realtime_data(symbols)
                    if data:
                        callback(data)
                except Exception as e:
                    print(f"轮询更新失败: {e}")
                time.sleep(60)  # 每分钟更新一次
        
        thread = threading.Thread(target=polling_loop, daemon=True)
        thread.start()


def create_yahoo_finance_source(delay: float = 0.5) -> YahooFinanceDataSource:
    """创建 Yahoo Finance 数据源实例"""
    return YahooFinanceDataSource(delay=delay)

