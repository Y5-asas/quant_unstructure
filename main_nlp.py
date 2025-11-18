import os
from pathlib import Path
from dotenv import load_dotenv
import itertools
from collections import defaultdict
import copy
import time

from tqdm import tqdm

from utils.get_prompt import get_sys_prompt, get_user_prompt
from utils.get_stocks_info import get_stocks_info, get_previous_k_dates
from utils.process_output import (
    process_llm_output,
    update_account_info,
    save_profit_info,
)
from utils.save_result import (
    save_all_llm_results,
    save_info_dict,
    load_info_dict,
    find_latest_ckpt_file,
    save_llm_raw_output,
)
from llm import *


load_dotenv()

# 获取项目根目录（main_nlp.py 所在目录）
BASE_DIR = Path(__file__).parent.resolve()

# 使用相对于项目根目录的路径
SAVE_ROOT_NUMERIC = str(BASE_DIR / "results")
SAVE_ROOT_NLP = str(BASE_DIR / "results_nlp")
INITIAL_CASH = 100000


# API 超时设置：连接超时 10 秒，读取超时 120 秒（LLM 生成可能需要较长时间）
API_TIMEOUT = (10.0, 120.0)

LLMs = {
    "qwen": {
        "client": OpenAI(
            api_key=os.getenv("QWEN_API_KEY"),
            base_url=os.getenv("QWEN_BASE_URL"),
            timeout=API_TIMEOUT,
        ),
        "function": qwen_client_response,
    },
    "deepseek": {
        "client": OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            timeout=API_TIMEOUT,
        ),
        "function": deepseek_client_response,
    },
    "kimi": {
        "client": OpenAI(
            api_key=os.getenv("KIMI_API_KEY"),
            base_url=os.getenv("KIMI_BASE_URL"),
            timeout=API_TIMEOUT,
        ),
        "function": kimi_client_response,
    },
    "chatglm": {
        "client": ZhipuAiClient(api_key=os.getenv("CHATGLM_API_KEY")),
        "function": chatglm_client_response,
    },
}


AccountInfoLLMs = defaultdict(dict)
ProfitInfoLLMs = defaultdict(dict)


def initialize_llm_info_nlp(
    llm_list,
    availableCash: float,
    positions={},
    resume_from_ckpt=True,
    ckpt_dir="ckpt/nlp/AccountInfoLLMs/",
    AccountInfoLLMs=None,
):
    if resume_from_ckpt:
        latest_file = find_latest_ckpt_file(ckpt_dir)
        if latest_file:
            print(f"[NLP] Loading from ckpt: {latest_file}")
            AccountInfoLLMs = load_info_dict(latest_file)
            return AccountInfoLLMs
    for llm in llm_list:
        AccountInfoLLMs[llm] = {
            "invoketime": 0,
            "last_trading_time": "2000-01-01",
            "totalReturnPercent": 0,
            "initialCash": availableCash,
            "availableCash": availableCash,
            "currentAccountValue": availableCash,
            "positions": positions,
        }
    return AccountInfoLLMs


def initialize_profit_info_nlp(
    resume_from_ckpt=True,
    ckpt_dir="ckpt/nlp/ProfitInfoLLMs/",
    ProfitInfoLLMs=None,
):
    if resume_from_ckpt:
        latest_file = find_latest_ckpt_file(ckpt_dir)
        if latest_file:
            ProfitInfoLLMs = load_info_dict(latest_file)
    return ProfitInfoLLMs


def market_trading_nlp(
    AccountInfoLLMs: dict,
    ProfitInfoLLMs: dict,
    stocks_dict: dict,
    history=10,
    debug=False,
    progress_callback=None,
):
    """
    与 main.py 中的 market_trading 类似，但额外保存 LLM 的自然语言行为日志。
    
    Args:
        progress_callback: Optional callback function(current_day, total_days, date) to update progress
    """
    if debug:
        stocks_dict = dict(itertools.islice(stocks_dict.items(), 15))
    max_retry = 20
    
    dates_list = list(stocks_dict.keys())
    total_days = len([d for d in dates_list if isinstance(d, str)]) - history
    
    for i, date in enumerate(stocks_dict):
        if i < history:
            continue
        
        # Update progress if callback provided
        if progress_callback:
            current_day = i - history + 1
            progress_callback(current_day, total_days, date)
        marketHistory, marketDataCurDay = get_previous_k_dates(
            stocks_dict, date, k=history
        )
        stocks_names = list(marketDataCurDay.keys())
        active_llms = [llm for llm in AccountInfoLLMs if llm in LLMs]

        for llm in tqdm(
            active_llms, desc=f"[NLP] 正在进行第{i+1}日交易 总计{len(stocks_dict)}日"
        ):
            if date in ProfitInfoLLMs[llm]:
                continue

            accouunt_info = AccountInfoLLMs[llm]
            sys_prompt = get_sys_prompt(stocks_names)
            user_prompt = get_user_prompt(
                marketHistory=marketHistory,
                marketToday=marketDataCurDay,
                current_time=date,
                **accouunt_info,
            )

            # 深拷贝账户状态，用于保存 before/after
            account_before = copy.deepcopy(AccountInfoLLMs[llm])
            process_content = {}
            content = ""
            retry = 0  # 每个LLM独立的重试计数
            while retry < max_retry:
                try:
                    content = LLMs[llm]["function"](
                        LLMs[llm]["client"], sys_prompt, user_prompt
                    )
                    # 处理输出结果 实现股票交易
                    process_content = process_llm_output(content, marketDataCurDay)
                    break
                except Exception as e:
                    print(f"[NLP][{llm}] Error: {e}, retry: {retry+1}/{max_retry}")
                    retry += 1
                    # 指数退避：等待时间 = 2^retry 秒，最多等待60秒
                    if retry < max_retry:
                        wait_time = min(2 ** retry, 60)
                        time.sleep(wait_time)
                    process_content = {}

            # 更新账户信息
            update_account_info(
                date, AccountInfoLLMs, llm, process_content, marketDataCurDay
            )
            account_after = copy.deepcopy(AccountInfoLLMs[llm])

            # 保存自然语言行为日志
            if content:  # 确保有内容才保存
                try:
                    save_llm_raw_output(
                        date=date,
                        llm=llm,
                        raw_content=content,
                        account_before=account_before,
                        account_after=account_after,
                        parsed_actions=process_content,
                        save_root=SAVE_ROOT_NLP,
                    )
                    print(f"[NLP] 已保存 {llm} 在 {date} 的决策日志到 {SAVE_ROOT_NLP}")
                except Exception as e:
                    print(f"[NLP] 保存 {llm} 在 {date} 的决策日志失败: {e}")
            else:
                print(f"[NLP] 警告: {llm} 在 {date} 的 content 为空，跳过保存")

        # 记录当日利润和资金（仍然保留数值信息，便于对比）
        save_profit_info(date, ProfitInfoLLMs, AccountInfoLLMs)
        save_info_dict(
            ProfitInfoLLMs, f"ckpt/nlp/ProfitInfoLLMs/{i+1}.json"
        )
        save_info_dict(
            AccountInfoLLMs, f"ckpt/nlp/AccountInfoLLMs/{i+1}.json"
        )

    # 保存运行结果的数值 CSV（确保路径正确）
    save_all_llm_results(ProfitInfoLLMs, SAVE_ROOT_NUMERIC)


if __name__ == "__main__":
    # 配置：一年期回测 + 多模型
    models = ["qwen", "deepseek", "kimi", "chatglm"]
    selected_llms = {m: LLMs[m] for m in models if m in LLMs}
    LLMs = selected_llms  # 覆盖全局 LLMs 为所选模型

    # 初始化账户与收益信息（不从 checkpoint 恢复）
    AccountInfoLLMs = initialize_llm_info_nlp(
        LLMs, INITIAL_CASH, AccountInfoLLMs=AccountInfoLLMs, resume_from_ckpt=False
    )
    ProfitInfoLLMs = initialize_profit_info_nlp(
        ProfitInfoLLMs=ProfitInfoLLMs, resume_from_ckpt=False
    ) or defaultdict(dict)

    # 获取一整年股票数据（根据 original_data 中的数据范围自行调整）
    stocks_dict, all_stocks_names = get_stocks_info(
        stocks_root="original_data/", start_date="2025-01-01", end_date="2025-12-31"
    )

    # 按日回测，并记录自然语言行为
    market_trading_nlp(AccountInfoLLMs, ProfitInfoLLMs, stocks_dict, history=10, debug=False)


