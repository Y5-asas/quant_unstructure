import os
import re
import json
import glob
from typing import Any, Dict

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
    except Exception:
        return None


def load_info_dict(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_info_dict(InfoDict: dict, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
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
    os.makedirs(save_root, exist_ok=True)
    for llm, profit_info in ProfitInfoLLMs.items():
        profit_df = transform_profit_info_to_df(profit_info)
        save_path = os.path.join(save_root, f"{llm}.csv")
        profit_df.to_csv(save_path, header=True, index=False)


def save_llm_raw_output(
    date: str,
    llm: str,
    raw_content: str,
    account_before: Dict[str, Any],
    account_after: Dict[str, Any],
    parsed_actions: Dict[str, Any],
    save_root: str = "results_nlp/",
):
    """
    保存 LLM 的原始自然语言输出及对应账户状态、解析后的动作。

    以 JSON Lines 形式追加到 results_nlp/{llm}_nlp.jsonl 中，便于后续分析。
    """
    # 确保 save_root 是绝对路径
    if not os.path.isabs(save_root):
        # 如果是相对路径，尝试从环境变量或当前工作目录解析
        # 优先使用传入的绝对路径
        from pathlib import Path
        # 如果 save_root 是 "results_nlp/" 这样的相对路径，需要找到项目根目录
        # 尝试从当前工作目录解析
        cwd = Path.cwd()
        # 检查是否是 quant_unstructure 目录
        if (cwd / "results_nlp").exists() or (cwd / "main_nlp.py").exists():
            base_dir = cwd
        else:
            # 否则使用文件所在目录的父目录（utils -> quant_unstructure）
            base_dir = Path(__file__).parent.parent.resolve()
        save_root = str(base_dir / save_root.replace("./", "").replace("results_nlp/", "results_nlp"))
    
    os.makedirs(save_root, exist_ok=True)
    record = {
        "date": date,
        "model": llm,
        "raw_output": raw_content,
        "parsed_actions": parsed_actions,
        "account_before": account_before,
        "account_after": account_after,
    }
    save_path = os.path.join(save_root, f"{llm}_nlp.jsonl")
    
    # 调试信息
    print(f"[save_llm_raw_output] 保存路径: {save_path}")
    print(f"[save_llm_raw_output] save_root: {save_root}")
    print(f"[save_llm_raw_output] 路径存在: {os.path.exists(os.path.dirname(save_path))}")
    print(f"[save_llm_raw_output] 目录已创建: {os.path.exists(save_root)}")
    
    try:
        with open(save_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")
        print(f"[save_llm_raw_output] ✅ 已保存 {llm} 在 {date} 的日志到 {save_path}")
    except Exception as e:
        print(f"[save_llm_raw_output] ❌ 保存失败: {e}")
        raise


