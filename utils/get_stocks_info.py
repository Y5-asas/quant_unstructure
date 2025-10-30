import os
import glob
import pandas as pd
from collections import defaultdict
from tqdm import tqdm


def read_one_stock_info(stock_path):
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


def get_stocks_info(stocks_root="original_data/"):
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
        stocks_raw_data[stock_name] = read_one_stock_info(stock_path)
    # 调整格式
    stocks_adjust_data = merge_all_stocks_info(stocks_raw_data)
    return stocks_adjust_data, stocks_names


if __name__ == "__main__":
    stocks_root = "original_data/"
    stocks = get_stocks_info(stocks_root)
    print(stocks)
