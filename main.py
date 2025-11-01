import os
import itertools
import random
from tqdm import tqdm
from collections import defaultdict

from utils.get_prompt import get_sys_prompt, get_user_prompt
from utils.get_stocks_info import get_stocks_info
from utils.process_output import (
    process_llm_output,
    update_account_info,
    save_profit_info,
)
from utils.save_result import save_all_llm_results
from llm import *

SAVE_ROOT = "results/"
INITIAL_CASH = 100000  # 初始现金
LLM = {
    "qwen": {
        "client": OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL),
        "function": qwen_client_response,
    },
    "deepseek": {
        "client": OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL),
        "function": deepseek_client_response,
    },
    "kimi": {
        "client": OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL),
        "function": kimi_client_response,
    },
    "chatglm": {
        "client": ZhipuAiClient(api_key=CHATGLM_API_KEY),
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


def initialize_llm_info(llm_list, availableCash: float, positions={}):
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


def market_trading(stocks_dict: dict, debug=False):
    """
    运行每日交易的函数
    """
    if debug:
        # stocks_dict = dict(random.sample(list(stocks_dict.items()), 5))
        stocks_dict = dict(itertools.islice(stocks_dict.items(), 5))
    retry, max_retry = 0, 20
    for i, date in enumerate(stocks_dict):
        marketData = stocks_dict[date]  # 当日全部股票数据
        # print(list(marketData.keys()))
        stocks_names = list(marketData.keys())
        responses = defaultdict(str)  # 回复结果字典
        for llm in tqdm(
            AccountInfoLLMs, desc=f"正在进行第{i+1}日交易 总计{len(stocks_dict)}日"
        ):
            # 获取当前llm的账户信息
            accouunt_info = AccountInfoLLMs[llm]
            # 获取prompt
            # sys_prompt = get_sys_prompt(stocks_names)
            sys_prompt = get_sys_prompt(stocks_names)
            user_prompt = get_user_prompt(marketData=marketData, **accouunt_info)
            while retry < max_retry:
                try:
                    # 结果存入回复字典
                    content = LLM[llm]["function"](
                        LLM[llm]["client"], sys_prompt, user_prompt
                    )
                    responses[llm] = content
                    # print(content)
                    # 处理输出结果 实现股票交易
                    process_content = process_llm_output(content, marketData)
                    break
                except Exception as e:
                    print(f"Error: {e}, retry: {retry}/{max_retry}")
                    retry += 1
                    process_content = {}
            update_account_info(date, AccountInfoLLMs[llm], process_content, marketData)
            # print(AccountInfoLLMs[llm])
            # 记录当日利润和资金
            save_profit_info(date, ProfitInfoLLMs, AccountInfoLLMs)
            # print(ProfitInfoLLMs[llm])
    # 保存运行结果
    save_all_llm_results(ProfitInfoLLMs, SAVE_ROOT)


if __name__ == "__main__":
    # 初始化所有配置
    # initialize_position()  # 初始化持仓情况
    initialize_llm_info(LLM, INITIAL_CASH)
    # print(ALL_LLM_INFO)

    # 获取股票每日的数据
    """
    stocks_dict = {
        'stock1': stcok1_df,
        ...
    }
    """
    stocks_dict, all_stocks_names = get_stocks_info(stocks_root="original_data/")
    # print(list(stocks_dict.keys()))

    # 开始迭代, 按日为单位, 每日获取股票数据输入进 llm 获取输出
    market_trading(stocks_dict, debug=True)
