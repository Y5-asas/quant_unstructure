import os
import glob
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime, timedelta


def read_one_stock_info(stock_path, start_date=None, end_date=None):
    """
    获取单个股票的数据
    读取 csv 返回字典 以时间为 key
    Return:
        {"2020-10-23": {"open": xxx, "close": xxx, ...}}
    """
    stock_dict = defaultdict(dict)
    stock_csv_info = pd.read_csv(stock_path)
    # date列确保为datetime格式
    # stock_csv_info["date"] = pd.to_datetime(stock_csv_info["date"])
    # 从早到晚排序
    stock_csv_info = stock_csv_info.sort_values(by="date", ascending=True).reset_index(
        drop=True
    )
    if start_date:
        stock_csv_info = stock_csv_info[stock_csv_info["date"] > start_date]
    if end_date:
        stock_csv_info = stock_csv_info[stock_csv_info["date"] < end_date]
    # print(stock_csv_info[:5])
    for index, row in stock_csv_info.iterrows():
        stock_dict[row["date"]] = {
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
            "code": row["thscode"],
        }
    return stock_dict


def merge_all_stocks_info(all_stocks_dict):
    """
    将全部股票的数据合并起来
    stocks_info_list:
        {
            "APPL": {"2020-10-23": {"open": xxx, "close": xxx, ...}},
            "BA": {"2020-10-23": {"open": xxx, "close": xxx, ...}},
            ...
        }
    Return:
        {
            "2020-10-23": {
                "APPL": {"open": xxx, "close": xxx, ...},
                "BA": {"open": xxx, "close": xxx, ...},
                ...
            },
            "2020-10-24": {...}
        }
    """
    adjust_stocks_dict = defaultdict(dict)
    for stock_code, date_data in all_stocks_dict.items():
        for date, stock_info in date_data.items():
            adjust_stocks_dict.setdefault(date, {})[stock_code] = stock_info
    return adjust_stocks_dict


def get_stocks_info(stocks_root="original_data/", start_date=None, end_date=None):
    """
    主函数, 获取全部股票数据
    """
    # 获取股票目录下的全部股票名称文件
    stocks_files = [f for f in os.listdir(stocks_root) if f.lower().endswith(".csv")]
    stocks_names = [f.split(".")[0] for f in stocks_files]
    # 汇总获取的全部股票数据
    stocks_raw_data = defaultdict(dict)
    for file in tqdm(stocks_files, desc="读取股票数据中"):
        stock_path = os.path.join(stocks_root, file)
        stock_name = file.split(".")[0]
        stocks_raw_data[stock_name] = read_one_stock_info(
            stock_path, start_date, end_date
        )
    # 调整格式
    stocks_adjust_data = merge_all_stocks_info(stocks_raw_data)
    return stocks_adjust_data, stocks_names


def get_previous_dates(start_date_str, days=10) -> list:
    # 将字符串转换为日期对象
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

    # 生成前10天的日期列表（从近到远排序）
    dates_list = []
    for i in range(days):
        date = start_date - timedelta(days=i)
        dates_list.append(date.strftime("%Y-%m-%d"))

    return dates_list


def get_previous_k_dates(stocks_dict, date, k=10) -> dict:
    """获取已知key及其前9个key的数据（共10个）"""
    # 获取所有key的列表
    dates = list(stocks_dict.keys())

    marketDataCurDay = stocks_dict[date]

    # 找到已知key的索引位置
    try:
        date_index = dates.index(date)
    except ValueError:
        return {}  # key不存在时返回空字典

    # 计算起始索引（确保不越界）
    start_index = max(0, date_index - k + 1)  # 往前取9个，加上当前key共10个
    end_index = date_index + 1

    # 获取这10个key
    target_dates = dates[start_index:end_index]

    # 返回对应的数据
    return {k: stocks_dict[k] for k in target_dates}, marketDataCurDay


def format_df_marketData(marketData: dict):
    columns = ["date", "open", "high", "low", "close", "volume", "code"]
    marketDataDFdict = defaultdict(lambda: pd.DataFrame(columns=columns))
    for i, date in enumerate(marketData):
        for stock in marketData[date]:
            new_row = marketData[date][stock].copy()
            new_row["date"] = date
            new_row["code"] = marketData[date][stock]["code"]
            if i == len(marketData) - 1:
                new_row["close"] = None
            marketDataDFdict[stock].loc[len(marketDataDFdict[stock])] = new_row
    marketDataDF = pd.concat(marketDataDFdict.values(), ignore_index=True)
    return marketDataDF


if __name__ == "__main__":
    stocks_root = "original_data/"
    stocks = get_stocks_info(stocks_root)
    print(stocks)
