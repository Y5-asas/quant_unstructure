"""
道琼斯30股票数据爬取工具
使用 yfinance 从 Yahoo Finance 获取每日股票数据
"""
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Optional
from tqdm import tqdm
import time

# 道琼斯30成分股列表（2024-2025年）
DOW_30_TICKERS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "UNH",   # UnitedHealth
    "GS",    # Goldman Sachs
    "HD",    # Home Depot
    "CAT",   # Caterpillar
    "MCD",   # McDonald's
    "V",     # Visa
    "HON",   # Honeywell
    "AMGN",  # Amgen
    "TRV",   # Travelers
    "AXP",   # American Express
    "JPM",   # JPMorgan Chase
    "CVX",   # Chevron
    "WMT",   # Walmart
    "MRK",   # Merck
    "DIS",   # Disney
    "PG",    # Procter & Gamble
    "IBM",   # IBM
    "DOW",   # Dow Inc
    "BA",    # Boeing
    "NKE",   # Nike
    "JNJ",   # Johnson & Johnson
    "VZ",    # Verizon
    "KO",    # Coca-Cola
    "MMM",   # 3M
    "INTC",  # Intel
    "CSCO",  # Cisco
    "WBA",   # Walgreens Boots Alliance
    "CRM",   # Salesforce
]


def fetch_single_stock_data(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取单个股票的历史数据
    
    Args:
        ticker: 股票代码，如 "AAPL"
        start_date: 开始日期 "YYYY-MM-DD"，如果提供则忽略 period
        end_date: 结束日期 "YYYY-MM-DD"，如果提供则忽略 period
        period: 时间周期，如 "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    
    Returns:
        DataFrame 包含列：date, open, high, low, close, adjusted_close, volume, dividend_amount, split_coefficient, thscode
    """
    try:
        stock = yf.Ticker(ticker)
        
        # 添加重试机制
        max_retries = 3
        hist = pd.DataFrame()
        for attempt in range(max_retries):
            try:
                if start_date and end_date:
                    hist = stock.history(start=start_date, end=end_date)
                elif period:
                    hist = stock.history(period=period)
                else:
                    # 默认获取最近1年的数据
                    hist = stock.history(period="1y")
                
                if not hist.empty:
                    break
                    
            except Exception as e:
                if "Rate limited" in str(e) or "Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 递增等待时间：5秒、10秒、15秒
                        print(f"  速率限制，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                raise
        
        if hist.empty:
            print(f"警告: {ticker} 没有获取到数据")
            return pd.DataFrame()
        
        # 重置索引，将日期转为列
        hist.reset_index(inplace=True)
        
        # 重命名列以匹配现有格式
        hist.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Dividends": "dividend_amount",
            "Stock Splits": "split_coefficient",
        }, inplace=True)
        
        # 添加 adjusted_close（如果没有则使用 close）
        if "Adj Close" in hist.columns:
            hist["adjusted_close"] = hist["Adj Close"]
        else:
            hist["adjusted_close"] = hist["close"]
        
        # 添加股票代码列
        hist["thscode"] = ticker
        
        # 格式化日期为字符串
        hist["date"] = pd.to_datetime(hist["date"]).dt.strftime("%Y-%m-%d")
        
        # 确保 dividend_amount 和 split_coefficient 存在
        if "dividend_amount" not in hist.columns:
            hist["dividend_amount"] = 0.0
        if "split_coefficient" not in hist.columns:
            hist["split_coefficient"] = 1.0
        
        # 选择并排序列
        columns_order = [
            "date", "open", "high", "low", "close", "adjusted_close",
            "volume", "dividend_amount", "split_coefficient", "thscode"
        ]
        hist = hist[columns_order]
        
        # 按日期排序
        hist = hist.sort_values("date", ascending=True).reset_index(drop=True)
        
        return hist
        
    except Exception as e:
        print(f"获取 {ticker} 数据时出错: {e}")
        return pd.DataFrame()


def fetch_dow30_daily_data(
    output_dir: str = "original_data/",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    update_existing: bool = True,
    delay: float = 2.0,  # 增加默认延迟到2秒，避免速率限制
) -> None:
    """
    获取道琼斯30所有成分股的每日数据并保存为CSV
    
    Args:
        output_dir: 输出目录，默认为 "original_data/"
        start_date: 开始日期 "YYYY-MM-DD"，如果为 None 则获取最近1年
        end_date: 结束日期 "YYYY-MM-DD"，如果为 None 则使用今天
        update_existing: 如果为 True，则更新现有文件（追加新数据）；如果为 False，则覆盖
        delay: 每次请求之间的延迟（秒），避免请求过快
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"开始获取道琼斯30成分股数据...")
    print(f"时间范围: {start_date or '最近1年'} 至 {end_date}")
    print(f"共 {len(DOW_30_TICKERS)} 只股票\n")
    
    for ticker in tqdm(DOW_30_TICKERS, desc="获取股票数据"):
        csv_path = os.path.join(output_dir, f"{ticker}.csv")
        
        try:
            # 获取新数据
            if start_date:
                new_data = fetch_single_stock_data(ticker, start_date=start_date, end_date=end_date)
            else:
                # 如果没有指定开始日期，获取最近1年
                new_data = fetch_single_stock_data(ticker, period="1y")
            
            if new_data.empty:
                print(f"跳过 {ticker}：没有获取到数据")
                continue
            
            if update_existing and os.path.exists(csv_path):
                # 读取现有数据
                try:
                    existing_data = pd.read_csv(csv_path)
                    existing_data["date"] = pd.to_datetime(existing_data["date"]).dt.strftime("%Y-%m-%d")
                    
                    # 合并数据，去重（保留新数据）
                    combined = pd.concat([existing_data, new_data], ignore_index=True)
                    combined = combined.drop_duplicates(subset=["date"], keep="last")
                    combined = combined.sort_values("date", ascending=True).reset_index(drop=True)
                    
                    # 保存
                    combined.to_csv(csv_path, index=False)
                    print(f"✓ {ticker}: 更新了 {len(new_data)} 条新数据，总计 {len(combined)} 条")
                except Exception as e:
                    print(f"警告: 读取 {ticker} 现有数据失败，将覆盖: {e}")
                    new_data.to_csv(csv_path, index=False)
                    print(f"✓ {ticker}: 保存了 {len(new_data)} 条数据（覆盖模式）")
            else:
                # 直接保存新数据
                new_data.to_csv(csv_path, index=False)
                print(f"✓ {ticker}: 保存了 {len(new_data)} 条数据")
            
            # 延迟，避免请求过快
            time.sleep(delay)
            
        except Exception as e:
            print(f"✗ {ticker}: 处理失败 - {e}")
            continue
    
    print(f"\n完成！数据已保存到 {output_dir}")


def fetch_latest_daily_data(
    output_dir: str = "original_data/",
    days: int = 1,
) -> None:
    """
    获取道琼斯30成分股的最新数据（用于每日定时任务）
    
    Args:
        output_dir: 输出目录
        days: 获取最近几天的数据（默认1天，即最新交易日）
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days + 5)).strftime("%Y-%m-%d")  # 多获取几天以防周末
    
    fetch_dow30_daily_data(
        output_dir=output_dir,
        start_date=start_date,
        end_date=end_date,
        update_existing=True,
        delay=2.0,  # 每日更新时使用2秒延迟
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="获取道琼斯30成分股数据")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="original_data/",
        help="输出目录（默认: original_data/）",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="开始日期 YYYY-MM-DD（默认: 最近1年）",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="结束日期 YYYY-MM-DD（默认: 今天）",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="仅获取最新数据（用于每日定时任务）",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="获取最近几天的数据（与 --latest 一起使用，默认: 1）",
    )
    
    args = parser.parse_args()
    
    if args.latest:
        print("获取最新数据模式...")
        fetch_latest_daily_data(output_dir=args.output_dir, days=args.days)
    else:
        fetch_dow30_daily_data(
            output_dir=args.output_dir,
            start_date=args.start_date,
            end_date=args.end_date,
        )

