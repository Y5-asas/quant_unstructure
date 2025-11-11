import json
from datetime import datetime, date
from typing import Dict, Iterable


def get_sys_prompt(stock_list, prompt_root="prompts/"):
    prompt_name = ["part2.txt", "part3.txt", "part4.txt"]
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

    for file_name in prompt_name:
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


def _format_number(value, precision: int = 4):
    if value is None:
        return "NA"
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return str(value)


def _format_series(series: Iterable, precision: int = 3) -> str:
    values = list(series or [])
    if not values:
        return "NA"
    return ", ".join(_format_number(val, precision=precision) for val in values)


def format_positions(positions: Dict) -> str:
    if not positions:
        return "No open positions."

    lines = []
    for symbol, info in positions.items():
        line = (
            f"- {symbol}: qty={_format_number(info.get('buy_in_num'))}, "
            f"entry={_format_number(info.get('buy_in_price'))}, "
            f"target={_format_number(info.get('profit_target'))}, "
            f"stop_loss={_format_number(info.get('stop_loss'))}"
        )
        lines.append(line)
    return "\n".join(lines)


def format_market_snapshot(market_today: Dict, include_indicators: bool = True) -> str:
    if not market_today:
        return "No market data available."

    sections = []
    for symbol in sorted(market_today.keys()):
        info = market_today[symbol]
        indicators = info.get("indicators", {}) if include_indicators else {}

        section_lines = [f"### {symbol}"]
        section_lines.append(
            "Prices: "
            f"open={_format_number(info.get('open'))}, "
            f"high={_format_number(info.get('high'))}, "
            f"low={_format_number(info.get('low'))}, "
            f"close={_format_number(info.get('close'))}"
        )
        section_lines.append(
            "Recent closes (oldest->newest)=["
            f"{_format_series(info.get('recent_closes'))}]"
        )
        section_lines.append(
            "Recent volumes (oldest->newest)=["
            f"{_format_series(info.get('recent_volumes'), precision=0)}]"
        )

        key_order = [
            "sma_5",
            "sma_10",
            "sma_20",
            "ema_5",
            "ema_10",
            "ema_20",
            "macd_macd",
            "macd_signal",
            "macd_hist",
            "rsi_14",
            "atr_14",
            "volatility_annualized",
        ]
        indicator_lines = [
            f"{key}={_format_number(indicators.get(key))}"
            for key in key_order
            if key in indicators
        ]
        if indicator_lines:
            section_lines.append("Indicators: " + ", ".join(indicator_lines))

        sections.append("\n".join(section_lines))

    return "\n\n".join(sections)


def get_user_prompt(
    last_trading_time,
    invoketime,
    marketHistory,
    marketToday,
    current_time,
    totalReturnPercent,
    availableCash,
    currentAccountValue,
    positions,
    initialCash,
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
    # current_time = date.today().isoformat()
    duringtime = iso_time_difference(last_trading_time, current_time)
    history_days = len(marketHistory) if marketHistory else 0
    user_prompt = f"""It has been {duringtime} days since you started trading.
The current time is {current_time}
You've been invoked {invoketime} times.

### DATA GRANULARITY
- All market data is **daily** frequency.
- Historical context includes the most recent {history_days} trading days available.

### CURRENT MARKET SNAPSHOT
{format_market_snapshot(marketToday)}

### ACCOUNT PERFORMANCE
- Current Total Return (percent): {_format_number(totalReturnPercent, precision=4)}
- Available Cash: {_format_number(availableCash, precision=2)}
- Current Account Value: {_format_number(currentAccountValue, precision=2)}

### OPEN POSITIONS
{format_positions(positions)}
"""
    return user_prompt


if __name__ == "__main__":
    # 测试

    # sys_prompt = get_sys_prompt(stock_list=["xxx", "sss"])
    # print(sys_prompt)

    mock_market = {
        "AAPL": {
            "open": 100,
            "high": 110,
            "low": 95,
            "close": 108,
            "volume": 1_000_000,
            "recent_closes": [95, 98, 102, 105, 108],
            "recent_volumes": [800_000, 820_000, 900_000, 950_000, 1_000_000],
            "indicators": {"ema_20": 101.2, "rsi_14": 62.5},
        }
    }
    user_prompt = get_user_prompt(
        last_trading_time="2025-10-27",
        invoketime=2,
        marketHistory={"2025-10-27": mock_market},
        marketToday=mock_market,
        current_time=date.today().isoformat(),
        totalReturnPercent=0.0234,
        availableCash=10023,
        currentAccountValue=42134,
        positions={
            "AAPL": {
                "buy_in_num": 100,
                "buy_in_price": 95.5,
                "profit_target": 120,
                "stop_loss": 90,
            }
        },
        initialCash=100000,
    )
    print(user_prompt)
