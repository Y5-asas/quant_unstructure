# 道琼斯30股票数据自动爬取指南

## 概述

本项目支持自动获取道琼斯30（Dow Jones 30）成分股的每日开盘价、收盘价等数据，使用 `yfinance` 库从 Yahoo Finance 获取数据。

## 安装依赖

首先需要安装 `yfinance` 库：

```bash
conda activate alpha_arena_env
pip install yfinance
```

## 使用方法

### 1. 手动获取数据

#### 获取最近1年的数据（首次使用）

```bash
cd /Users/y5/Downloads/alpha_arena/quant_unstructure
python utils/fetch_dow30_data.py
```

#### 获取指定时间范围的数据

```bash
python utils/fetch_dow30_data.py --start-date 2024-01-01 --end-date 2024-12-31
```

#### 仅获取最新数据（用于每日更新）

```bash
python utils/fetch_dow30_data.py --latest --days 1
```

### 2. 自动每日更新（推荐）

#### macOS/Linux 使用 Crontab

1. 编辑 crontab：
```bash
crontab -e
```

2. 添加以下行（每天下午6点运行，交易结束后）：
```bash
0 18 * * 1-5 /Users/y5/Downloads/alpha_arena/quant_unstructure/scripts/daily_fetch_dow30.sh
```

注意：
- `18` 表示下午6点（18:00）
- `1-5` 表示周一到周五（交易日）
- 请根据实际情况修改脚本路径

3. 或者使用 Python 脚本直接运行：
```bash
0 18 * * 1-5 cd /Users/y5/Downloads/alpha_arena/quant_unstructure && conda run -n alpha_arena_env python utils/fetch_dow30_data.py --latest --days 1
```

#### Windows 使用任务计划程序

1. 打开"任务计划程序"（Task Scheduler）
2. 创建基本任务
3. 设置触发器：每天，下午6点
4. 设置操作：启动程序
   - 程序：`C:\Users\YourName\anaconda3\envs\alpha_arena_env\python.exe`
   - 参数：`utils/fetch_dow30_data.py --latest --days 1`
   - 起始于：`C:\path\to\alpha_arena\quant_unstructure`

## 道琼斯30成分股列表

当前支持以下30只股票：

- AAPL (Apple)
- MSFT (Microsoft)
- UNH (UnitedHealth)
- GS (Goldman Sachs)
- HD (Home Depot)
- CAT (Caterpillar)
- MCD (McDonald's)
- V (Visa)
- HON (Honeywell)
- AMGN (Amgen)
- TRV (Travelers)
- AXP (American Express)
- JPM (JPMorgan Chase)
- CVX (Chevron)
- WMT (Walmart)
- MRK (Merck)
- DIS (Disney)
- PG (Procter & Gamble)
- IBM (IBM)
- DOW (Dow Inc)
- BA (Boeing)
- NKE (Nike)
- JNJ (Johnson & Johnson)
- VZ (Verizon)
- KO (Coca-Cola)
- MMM (3M)
- INTC (Intel)
- CSCO (Cisco)
- WBA (Walgreens Boots Alliance)
- CRM (Salesforce)

## 数据格式

获取的数据会保存为 CSV 文件，格式与现有数据兼容：

```csv
date,open,high,low,close,adjusted_close,volume,dividend_amount,split_coefficient,thscode
2025-01-15,150.25,152.30,149.80,151.50,151.50,25000000,0.0,1.0,AAPL
```

## 注意事项

1. **数据延迟**：Yahoo Finance 的数据通常在交易结束后才会更新，建议在每天下午6点后运行
2. **请求频率**：脚本已内置延迟（0.5秒/请求），避免请求过快被限制
3. **数据质量**：如果某些股票数据缺失，脚本会跳过并继续处理其他股票
4. **网络问题**：如果网络不稳定，可能需要多次运行才能获取完整数据

## 故障排查

### 问题：某些股票数据获取失败

**解决方案**：
- 检查网络连接
- 确认股票代码是否正确
- 尝试单独获取该股票：`python -c "from utils.fetch_dow30_data import fetch_single_stock_data; print(fetch_single_stock_data('AAPL', period='1y'))"`

### 问题：数据格式不匹配

**解决方案**：
- 检查 CSV 文件是否包含所有必需列
- 确认日期格式为 `YYYY-MM-DD`
- 查看 `utils/fetch_dow30_data.py` 中的列名映射

### 问题：定时任务不运行

**解决方案**：
- 检查 crontab 语法是否正确
- 确认脚本有执行权限：`chmod +x scripts/daily_fetch_dow30.sh`
- 查看日志文件：`logs/daily_fetch.log`
- 手动运行脚本测试

## 与 nof1.ai 的对比

nof1.ai 项目使用实时数据爬取，本项目当前实现的是：
- **每日批量更新**：适合回测场景，每天获取一次完整数据
- **历史数据支持**：可以获取任意时间范围的历史数据
- **可扩展为实时**：`utils/yfinance_data_source.py` 提供了实时数据接口（预留）

如果需要实时数据，可以：
1. 使用 `YahooFinanceDataSource` 类的 `get_realtime_data()` 方法
2. 设置更频繁的定时任务（如每小时）
3. 使用 WebSocket 订阅（需要额外实现）

