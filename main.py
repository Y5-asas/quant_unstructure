import os

from utils.get_prompt import get_sys_prompt, get_user_prompt
from utils.get_stocks_info import get_stocks_info
from llm import *

LLM_LIST = ["qwen", "deepseek", "kimi", "chat_glm"]
ALL_LLM_INFO = {}
INITIAL_CASH = 10000  # 初始现金
INITIAL_POS = {}  # 初始持仓情况


def initialize_position():
    """
    初始化初始持仓情况, 包含因素待定
    """
    ...


def initialize_llm_info(llm_list, availableCash, positions):
    """
    初始化所有 LLM 的资金和持仓情况
    因素待定，可添加
    """
    for llm in llm_list:
        ALL_LLM_INFO[llm] = {
            "invoketime": 0,
            "totalReturnPercent": 0,
            "availableCash": availableCash,
            "currentAccountValue": availableCash,
            "positions": positions,
        }


def market_trading():
    """
    运行每日交易的函数
    """


if __name__ == "__main__":
    # 初始化所有配置
    initialize_position()  # 初始化持仓情况
    initialize_llm_info(LLM_LIST, INITIAL_CASH, INITIAL_POS)
    # print(ALL_LLM_INFO)

    # 获取股票每日的数据
    """
    stocks_dict = {
        'stock1': stcok1_df,
        ...
    }
    """
    stocks_dict = get_stocks_info

    # 开始迭代, 按日为单位, 每日获取股票数据输入进 llm 获取输出
    market_trading()
