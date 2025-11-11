import json
from .fix_json import smart_fix_json


def process_llm_output(content: str, marketDataCurDay: dict):
    """
    处理 LLM 的输出内容
    content: str 格式的 json 字符串
    格式:
        {
        "CSCO": {
            "trade_signal_args": {
            "coin": "CSCO",     股票代码
            "signal": "entry",  买入卖出信号
            "profit_target": 25.5,  盈利目标，如果单支股价＞=这个数立刻卖出
            "stop_loss": 23.8,  止损目标，如果单支股价＜=这个数立刻卖出
            "invalidation_condition": "If price closes below 23.8 on a 3-minute candle",
            "leverage": 10,     杠杆系数，暂且不用
            "confidence": 0.72,     置信度
            "risk_usd": 500,    愿意承担的风险金额
            "justification": "CSCO is showing strength above key support at 23.8 with a solid close near the high of the day. Volume is strong, indicating accumulation. Entering with a tight stop and target aligned with recent resistance."
            }
            买入股数 = 愿意承担的风险金额 / (当前股价 - 止损目标)
        },
        ...
    """
    # content: dict = json.loads(content)
    content: dict = smart_fix_json(content)

    # 计算每只股票该买入/卖出多少
    for stock, info in content.items():
        # print(f"=========", content[stock])
        # content[stock]["change_num"] = content[stock]["risk_usd"] / (
        #     marketData[stock]["open"] - content[stock]["stop_loss"]
        # )
        open_price = marketDataCurDay[stock]["open"]
        # open_price = marketData[
        #     (marketData["code"] == stock) & (marketData["date"] == date)
        # ]["open"]
        content[stock]["change_num"] = content[stock]["change_value"] / open_price
        content[stock]["current_price"] = open_price

    return content


def update_profit(AccountInfoLLMs: dict, llm: str, marketDataCurDay: dict):
    cur_pos: dict = AccountInfoLLMs[llm]["positions"]
    account_value = AccountInfoLLMs[llm]["availableCash"]
    for stock, info in cur_pos.items():
        # 计算股票价值
        account_value += marketDataCurDay[stock]["open"] * info["buy_in_num"]
    return_ratio = (
        account_value - AccountInfoLLMs[llm]["initialCash"]
    ) / AccountInfoLLMs[llm]["initialCash"]
    AccountInfoLLMs[llm]["currentAccountValue"] = account_value
    AccountInfoLLMs[llm]["totalReturnPercent"] = return_ratio


def update_account_info(
    date: str, AccountInfoLLMs: dict, llm: str, content: dict, marketDataCurDay: dict
):
    """
    date: str 格式交易时间 如: 2020-10-23
    AccountInfo: llm 的账户信息
    content: 模型的股票评估结果 经过 process_llm_output() 函数处理的输出数据
    """
    for stock, info in content.items():
        # check 当前价格, 如果大于profit_target或小于stop_loss就卖出
        ...
        # 执行当前交易日的买卖
        if info["signal"] == "entry":
            # cost = info["change_num"] * info["current_price"]  # 计算买入花销
            cost = info["change_value"]
            if cost <= AccountInfoLLMs[llm]["availableCash"]:
                AccountInfoLLMs[llm]["invoketime"] += 1  # 交易次数+1
                AccountInfoLLMs[llm]["last_trading_time"] = date  # 更新最后交易时间
                AccountInfoLLMs[llm]["availableCash"] -= cost  # 支出
                cur_pos = AccountInfoLLMs[llm]["positions"].get(
                    stock, {}
                )  # 当前这只股票的持仓情况
                AccountInfoLLMs[llm]["positions"][stock] = {
                    "buy_in_price": info["current_price"],  # 买入价
                    "buy_in_num": info["change_num"]
                    + cur_pos.get("buy_in_num", 0),  # 买入数量
                    "profit_target": info["profit_target"],  # 盈利价格
                    "stop_loss": info["stop_loss"],  # 止损价格
                }
            else:
                print(
                    f"现金不足, 买入 {stock} 需要: {cost}, 当前可用现金: {AccountInfoLLMs[llm]['availableCash']}"
                )
        elif info["signal"] == "close":
            cur_pos = AccountInfoLLMs[llm]["positions"].get(stock, {})
            if cur_pos:
                AccountInfoLLMs[llm]["invoketime"] += 1
                AccountInfoLLMs[llm]["last_trading_time"] = date
                sell = cur_pos["buy_in_num"] * info["current_price"]  # 卖出价格
                AccountInfoLLMs[llm]["availableCash"] += sell
                AccountInfoLLMs[llm]["positions"].pop(
                    stock
                )  # 卖出股票,  从当前持有资产删除
        else:  # 模型输出错误
            if info["signal"] != "hold":
                print(f"模型 signal 输出错误, signal: {info['signal']}")

    # 更新资产, 计算利润
    update_profit(AccountInfoLLMs, llm, marketDataCurDay)


def save_profit_info(date: str, ProfitInfoLLMs: dict, AccountInfoLLMs: dict):
    for llm, account_info in AccountInfoLLMs.items():
        ProfitInfoLLMs[llm][date] = {
            "totalReturnPercent": account_info["totalReturnPercent"],
            "availableCash": account_info["availableCash"],
            "currentAccountValue": account_info["currentAccountValue"],
            "positions": account_info["positions"],
        }
