import os
import pandas as pd


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
