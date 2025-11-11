import os
import re
import json
import glob
import pandas as pd


def find_latest_ckpt_file(folder_path):
    """
    找到最新的 json 文件
    """
    try:
        return max(
            [
                f
                for f in glob.glob(os.path.join(folder_path, "*.json"))
                if re.match(r".*/\d+\.json$", f)
            ],
            key=lambda x: int(re.search(r"/(\d+)\.json$", x).group(1)),
        )
    except:
        return None


def load_info_dict(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_info_dict(InfoDict: dict, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(InfoDict, f, ensure_ascii=False, indent=4)


def transform_profit_info_to_df(ProfitInfo: dict):
    """
    处理一个 llm 的每日盈利信息
    ProfitInfo: {
        "2020-10-23": {
            "totalReturnPercent": 当日利润率,
            "availableCash": 可用现金,
            "currentAccountValue": 当日账户价值,
            "positions": 当日资产配置,
        },
    }
    """
    df = pd.DataFrame(
        columns=["Date", "ReturnPercent", "AvailableCash", "AccountValue"]
    )
    for date, info in ProfitInfo.items():
        new_row = {
            "Date": date,
            "ReturnPercent": info["totalReturnPercent"],
            "AvailableCash": info["availableCash"],
            "AccountValue": info["currentAccountValue"],
        }
        df.loc[len(df)] = new_row
    # 排序, 保证时间顺序从早到晚
    df_sorted = df.sort_values("Date")
    return df_sorted


def save_all_llm_results(ProfitInfoLLMs: dict, save_root="result/"):
    """
    处理全部 llm 的盈利信息, 并保存为 csv
    ProfitInfoLLMs: {
        "qwen": {
            "2020-10-23": {
                "totalReturnPercent": 当日利润率,
                "availableCash": 可用现金,
                "currentAccountValue": 当日账户价值,
                "positions": 当日资产配置,
            },...
        },...
    }
    """
    for llm, profit_info in ProfitInfoLLMs.items():
        profit_df = transform_profit_info_to_df(profit_info)
        save_path = os.path.join(save_root, f"{llm}.csv")
        profit_df.to_csv(save_path, header=True, index=False)
