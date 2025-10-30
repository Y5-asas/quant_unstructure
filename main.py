import os
import itertools
from collections import defaultdict

from utils.get_prompt import get_sys_prompt, get_user_prompt
from utils.get_stocks_info import get_stocks_info
from llm import *

INITIAL_CASH = 10000  # 初始现金
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
AccountInfoLLMs = {}


def initialize_position(stocks_names):
    """
    初始化初始持仓情况, 包含因素待定
    """
    initialize_pos = defaultdict(dict)
    for name in stocks_names:
        initialize_pos[name] = {"holdings": 0, "currentStockPrice": 0, "totalValue": 0}
    return initialize_pos


def initialize_llm_info(llm_list, availableCash, positions={}):
    """
    初始化所有 LLM 的资金和持仓情况
    因素待定，可添加
    """
    for llm in llm_list:
        AccountInfoLLMs[llm] = {
            "invoketime": 0,
            "last_trading_time": "2000-01-01",
            "totalReturnPercent": 0,
            "availableCash": availableCash,
            "currentAccountValue": availableCash,
            "positions": positions,
        }


def market_trading(stocks_names: list, stocks_dict: dict, debug=False):
    """
    运行每日交易的函数
    """
    if debug:
        stocks_dict = dict(itertools.islice(stocks_dict.items(), 5))
    for date in stocks_dict:
        marketData = stocks_dict[date]  # 当日全部股票数据
        responses = defaultdict(str)  # 回复结果字典
        for llm in AccountInfoLLMs:
            # 获取当前llm的账户信息
            accouunt_info = AccountInfoLLMs[llm]
            # 获取prompt
            sys_prompt = get_sys_prompt(stocks_names)
            user_prompt = get_user_prompt(marketData=marketData, **accouunt_info)
            # 结果存入回复字典
            responses[llm] = LLM[llm]["function"](
                LLM[llm]["client"], sys_prompt, user_prompt
            )
            # 处理输出结果 实现股票交易


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
    stocks_dict, stocks_names = get_stocks_info(stocks_root="original_data/")
    # print(list(stocks_dict.keys()))

    # 开始迭代, 按日为单位, 每日获取股票数据输入进 llm 获取输出
    market_trading(stocks_names, stocks_dict, debug=True)
