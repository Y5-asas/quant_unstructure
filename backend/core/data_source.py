"""股票数据源抽象（预留实时股票接口）"""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from backend.core.models import RealtimeStockData
from backend.config import BASE_DIR, ORIGINAL_DATA_DIR


class StockDataSource:
    """股票数据源抽象基类"""
    
    def get_realtime_data(self, symbols: List[str]) -> Dict[str, RealtimeStockData]:
        """
        获取实时股票数据（预留接口）
        
        Args:
            symbols: 股票代码列表，如 ["AAPL", "MSFT"]
            
        Returns:
            股票代码到实时数据的映射
        """
        # TODO: 实现实时数据获取
        # 可能的实现：
        # - Yahoo Finance API
        # - Alpha Vantage
        # - Tushare（国内）
        # - 自建数据采集服务
        raise NotImplementedError("实时数据接口待实现")
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取历史股票数据（预留接口）
        
        Args:
            symbol: 股票代码，如 "AAPL"
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"
            
        Returns:
            包含日期、开盘、收盘等信息的 DataFrame
        """
        # TODO: 实现历史数据获取
        raise NotImplementedError("历史数据接口待实现")
    
    def subscribe_updates(self, symbols: List[str], callback: callable):
        """
        订阅实时更新（预留接口）
        
        Args:
            symbols: 股票代码列表
            callback: 数据更新回调函数
        """
        # TODO: 实现实时订阅
        raise NotImplementedError("实时订阅接口待实现")


class LocalStockDataSource(StockDataSource):
    """本地CSV文件数据源（当前使用）"""
    
    def get_realtime_data(self, symbols: List[str]) -> Dict[str, RealtimeStockData]:
        """当前不支持实时数据，抛出异常"""
        raise NotImplementedError("本地数据源不支持实时数据，请使用实时数据源")
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """从本地CSV文件读取历史数据"""
        csv_path = ORIGINAL_DATA_DIR / f"{symbol}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"股票 {symbol} 的数据文件不存在: {csv_path}")
        
        df = pd.read_csv(csv_path)
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        return df.sort_values("date").reset_index(drop=True)


# 全局数据源实例（当前使用本地数据源）
stock_data_source: StockDataSource = LocalStockDataSource()


def get_stock_data_source() -> StockDataSource:
    """获取当前配置的数据源"""
    return stock_data_source


def set_stock_data_source(source: StockDataSource):
    """设置数据源（用于切换实时数据源）"""
    global stock_data_source
    stock_data_source = source

