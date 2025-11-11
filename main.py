import os
from dotenv import load_dotenv
import itertools
import random
from tqdm import tqdm
from collections import defaultdict
import concurrent.futures

from utils.get_prompt import get_sys_prompt, get_user_prompt
from utils.get_stocks_info import (
    get_stocks_info,
    get_previous_dates,
    get_previous_k_dates,
    format_df_marketData,
)
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
)
from llm import *

# 加载当前目录下的.env文件
load_dotenv()

SAVE_ROOT = "results/"
INITIAL_CASH = 100000  # 初始现金
LLMs = {
    "qwen": {
        "client": OpenAI(
            api_key=os.getenv("QWEN_API_KEY"), base_url=os.getenv("QWEN_BASE_URL")
        ),
        "function": qwen_client_response,
    },
    "deepseek": {
        "client": OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
        ),
        "function": deepseek_client_response,
    },
    "kimi": {
        "client": OpenAI(
            api_key=os.getenv("KIMI_API_KEY"), base_url=os.getenv("KIMI_BASE_URL")
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
"""
AccountInfoLLMs: {
    "qwen": {
        "invoketime": 交易次数,
        "last_trading_time": 上次交易时间,
        "totalReturnPercent": 总利润率,
        "initialCash": 初始现金,
        "availableCash": 可用现金,
        "currentAccountValue": 当前账户价值,
        "positions": 资产配置,
    }.
}

ProfitInfoLLMs: {
    "qwen": {
        "2020-10-23": {
            "totalReturnPercent": 当日利润率,
            "availableCash": 可用现金,
            "currentAccountValue": 当日账户价值,
            "positions": 当日资产配置,
        },
    }
}
"""


def initialize_position(stocks_names):
    """
    初始化初始持仓情况, 包含因素待定
    """
    initialize_pos = defaultdict(dict)
    for name in stocks_names:
        initialize_pos[name] = {"holdings": 0, "currentStockPrice": 0, "totalValue": 0}
    return initialize_pos


def initialize_llm_info(
    llm_list,
    availableCash: float,
    positions={},
    resume_from_ckpt=True,
    ckpt_dir="ckpt/AccountInfoLLMs/",
    AccountInfoLLMs=None,
):
    """
    初始化所有 LLM 的资金和持仓情况
    因素待定，可添加
    positions:
        {
            'buy_in_price': xxx,    # 买入价
            'buy_in_num': xxx,      # 买入数量
            'profit_target': xxx,   # 盈利价格
            'stop_loss': xxx,       # 止损价格
        }
    """
    if resume_from_ckpt:
        latest_file = find_latest_ckpt_file(ckpt_dir)
        if latest_file:
            # path = os.path.join(ckpt_dir, latest_file)
            print(f"Loading from ckptpoint: {latest_file}")
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


def initialize_profit_info(
    resume_from_ckpt=True, ckpt_dir="ckpt/ProfitInfoLLMs/", ProfitInfoLLMs=None
):
    if resume_from_ckpt:
        latest_file = find_latest_ckpt_file(ckpt_dir)
        if latest_file:
            # path = os.path.join(ckpt_dir, latest_file)
            ProfitInfoLLMs = load_info_dict(latest_file)
    return ProfitInfoLLMs


def market_trading(
    AccountInfoLLMs: dict,
    ProfitInfoLLMs: dict,
    stocks_dict: dict,
    history=10,
    debug=False,
):
    """
    运行每日交易的函数
    """
    if debug:
        # stocks_dict = dict(random.sample(list(stocks_dict.items()), 5))
        stocks_dict = dict(itertools.islice(stocks_dict.items(), 15))
    retry, max_retry = 0, 20
    for i, date in enumerate(stocks_dict):
        if i < history:
            continue
        # marketData = stocks_dict[date]  # 当日全部股票数据
        marketData, marketDataCurDay = get_previous_k_dates(
            stocks_dict, date, k=history
        )
        # print(marketData)
        # print(list(marketData.keys()))
        marketData = format_df_marketData(marketData)
        # 获取纯字符串形式 df
        marketData_str = marketData.to_string(
            max_rows=None,  # 显示所有行
            max_cols=None,  # 显示所有列
            line_width=None,  # 不限制宽度
            max_colwidth=None,  # 不限制列宽
        )
        # print(marketData)
        stocks_names = list(marketDataCurDay.keys())
        # stocks_names = list(set(marketData["code"]))
        responses = defaultdict(str)  # 回复结果字典
        for llm in tqdm(
            AccountInfoLLMs, desc=f"正在进行第{i+1}日交易 总计{len(stocks_dict)}日"
        ):
            # check是否已经交易过
            if date in ProfitInfoLLMs[llm]:
                continue
            # 获取当前llm的账户信息
            accouunt_info = AccountInfoLLMs[llm]
            # 获取prompt
            sys_prompt = get_sys_prompt(stocks_names)
            user_prompt = get_user_prompt(
                marketData=marketData_str, current_time=date, **accouunt_info
            )
            # with open("prompt_user.txt", "w", encoding="utf-8") as f:
            #     f.write(user_prompt)
            # print(user_prompt)
            while retry < max_retry:
                try:
                    # 结果存入回复字典
                    content = LLMs[llm]["function"](
                        LLMs[llm]["client"], sys_prompt, user_prompt
                    )
                    responses[llm] = content
                    # print(content)
                    # 处理输出结果 实现股票交易
                    process_content = process_llm_output(content, marketDataCurDay)
                    break
                except Exception as e:
                    print(f"Error: {e}, retry: {retry}/{max_retry}")
                    retry += 1
                    process_content = {}
            # 更新 llm 的账户信息
            update_account_info(
                date, AccountInfoLLMs, llm, process_content, marketDataCurDay
            )
            # print(AccountInfoLLMs[llm])
        # 记录当日利润和资金
        save_profit_info(date, ProfitInfoLLMs, AccountInfoLLMs)
        # print(ProfitInfoLLMs[llm])
        # 每日保存ckpt
        save_info_dict(ProfitInfoLLMs, f"ckpt/ProfitInfoLLMs/{i+1}.json")
        save_info_dict(AccountInfoLLMs, f"ckpt/AccountInfoLLMs/{i+1}.json")

        # 保存运行结果 每隔10个交易日保存一次
        if i % 10 == 0:
            save_all_llm_results(ProfitInfoLLMs, SAVE_ROOT)
    save_all_llm_results(ProfitInfoLLMs, SAVE_ROOT)


def process_single_llm(
    llm, marketData, marketDataCurDay, stocks_names, date, max_retry=20
):
    """
    处理单个LLM的交易逻辑
    """
    if date in ProfitInfoLLMs[llm]:
        return
    retry = 0
    accouunt_info = AccountInfoLLMs[llm]
    sys_prompt = get_sys_prompt(stocks_names)
    user_prompt = get_user_prompt(
        marketData=marketData, current_time=date, **accouunt_info
    )

    while retry < max_retry:
        try:
            content = LLMs[llm]["function"](
                LLMs[llm]["client"], sys_prompt, user_prompt
            )
            process_content = process_llm_output(content, marketDataCurDay)
            return llm, content, process_content, None
        except Exception as e:
            print(f"Error for {llm}: {e}, retry: {retry}/{max_retry}")
            retry += 1

    return llm, "", {}, Exception(f"Max retries exceeded for {llm}")


def market_trading_parallel(
    AccountInfoLLMs: dict,
    ProfitInfoLLMs: dict,
    stocks_dict: dict,
    history=10,
    debug=False,
    max_workers=len(LLMs),
):
    """
    运行每日交易的函数（并行版本）
    """
    if debug:
        stocks_dict = dict(itertools.islice(stocks_dict.items(), 15))

    for i, date in enumerate(stocks_dict):
        if i < history:
            continue
        # marketData = stocks_dict[date]
        marketData, marketDataCurDay = get_previous_k_dates(
            stocks_dict, date, k=history
        )
        marketData = format_df_marketData(marketData)
        # 获取纯字符串形式 df
        marketData_str = marketData.to_string(
            max_rows=None,  # 显示所有行
            max_cols=None,  # 显示所有列
            line_width=None,  # 不限制宽度
            max_colwidth=None,  # 不限制列宽
            index=False,
        )
        stocks_names = list(marketDataCurDay.keys())
        responses = defaultdict(str)

        # 使用线程池并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_llm = {
                executor.submit(
                    process_single_llm,
                    llm,
                    marketData_str,
                    marketDataCurDay,
                    stocks_names,
                    date,
                ): llm
                for llm in AccountInfoLLMs
            }

            # 使用tqdm显示进度
            futures = list(future_to_llm.keys())
            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc=f"正在进行第{i+1}日交易 总计{len(stocks_dict)}日",
            ):
                llm, content, process_content, error = future.result()

                if error is None:
                    responses[llm] = content
                    # 更新账户信息（注意线程安全）
                    update_account_info(
                        date, AccountInfoLLMs[llm], llm, process_content, marketData
                    )
                else:
                    print(f"Failed to process {llm}: {error}")

        # 记录当日利润和资金
        save_profit_info(date, ProfitInfoLLMs, AccountInfoLLMs)
        # 每日保存ckpt
        save_info_dict(ProfitInfoLLMs, f"ckpt/ProfitInfoLLMs/{i+1}.json")
        save_info_dict(AccountInfoLLMs, f"ckpt/AccountInfoLLMs/{i+1}.json")
    # 保存运行结果
    save_all_llm_results(ProfitInfoLLMs, SAVE_ROOT)


if __name__ == "__main__":
    # 初始化所有配置
    model = "qwen"  # 根据自己负责的模型填入 ['qwen', 'deepseek', 'kimi', 'chatglm']
    LLMs = {model: LLMs[model]}

    # initialize_position()  # 初始化持仓情况
    AccountInfoLLMs = initialize_llm_info(
        LLMs, INITIAL_CASH, AccountInfoLLMs=AccountInfoLLMs
    )
    ProfitInfoLLMs = initialize_profit_info(ProfitInfoLLMs=ProfitInfoLLMs)
    # print(AccountInfoLLMs)
    # printProfitInfoLLMs

    # 获取股票每日的数据
    """
    stocks_dict = {
        'stock1': stcok1_df,
        ...
    }
    """
    stocks_dict, all_stocks_names = get_stocks_info(
        stocks_root="original_data/", start_date="2025-01-01", end_date="2025-04-29"
    )
    # print(list(stocks_dict.keys()))

    # 开始迭代, 按日为单位, 每日获取股票数据输入进 llm 获取输出
    market_trading(AccountInfoLLMs, ProfitInfoLLMs, stocks_dict, debug=True)  # 单线程
    # market_trading_parallel(
    #     AccountInfoLLMs, ProfitInfoLLMs, stocks_dict, debug=True, max_workers=4
    # )  # 多线程并行
