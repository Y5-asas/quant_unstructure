import json
from datetime import datetime, date


def get_sys_prompt(stock_list):
    prompt_root = "AlphaArena/prompts/"
    prompt_path = ["part2.txt", "part3.txt", "part4.txt"]
    prompt_p1 = f"""## HARD CONSTRAINTS

### Position Limits
- Tradable coins: {stock_list}
- Maximum {len(stock_list)} concurrent positions
- No pyramiding or adding to existing positions
- Must be flat before re-entering a coin

### Risk Management
- Maximum risk per trade: 5% of account value
- Leverage range: 5x to 40x
- Minimum risk-reward ratio: 2:1
- Every position must have:
  - Stop loss (specific price level)
  - Profit target (specific price level)  
  - Invalidation condition (format: "If price closes below/above [PRICE] on a [TIMEFRAME] candle")
"""
    prompts = [prompt_p1]

    for file_name in prompt_path:
        file_path = prompt_root + file_name
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        prompts.append(content)

    return "\n".join(prompts)


def iso_time_difference(iso_date1, iso_date2):
    """
    计算两个ISO格式时间字符串的差值
    返回：timedelta对象
    """
    # 将ISO字符串转换为datetime对象
    date1 = datetime.fromisoformat(iso_date1).date()
    date2 = datetime.fromisoformat(iso_date2).date()

    # 计算差值
    diff = date2 - date1
    return diff.days


def get_user_prompt(
    last_trading_time,
    invoketime,
    marketData,
    totalReturnPercent,
    availableCash,
    currentAccountValue,
    positions,
):
    """
    args:
        - last_trading_time: 上次交易的时间 iso 格式
        - invoketime: 调用次数(不包括这次)
        - marketData: 当前市场数据(json 格式)
        - totalReturnPercent: 总收益率百分比​
        - availableCash: 可用现金余额
        - currentAccountValue: 当前账户总价值（现金 + 持仓市值）
        - positions: 当前持仓详情 json 格式
    """
    current_time = date.today().isoformat()
    duringtime = iso_time_difference(last_trading_time, current_time)
    user_prompt = f"""It has been {duringtime} days since you started trading.
The current time is {current_time} 
You've been invoked {invoketime} times.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST - NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series 
are provided at 3 minute intervals. If a coin uses a different interval, it is 
explicitly stated in that coin's section.

**CURRENT MARKET STATE FOR ALL COINS**
{marketData}

**HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE**
Current Total Return (percent): {totalReturnPercent}
Available Cash: {availableCash}
Current Account Value: {currentAccountValue}

Current live positions & performance:
{positions}
"""
    return user_prompt


if __name__ == "__main__":
    # 测试

    # sys_prompt = get_sys_prompt(stock_list=["xxx", "sss"])
    # print(sys_prompt)

    user_prompt = get_user_prompt(
        last_trading_time="2025-10-27",
        invoketime=2,
        marketData="xxx",
        totalReturnPercent="2%",
        availableCash=10023,
        currentAccountValue=42134,
        positions="xxx",
    )
    print(user_prompt)
