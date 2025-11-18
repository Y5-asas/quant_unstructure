# Alpha Arena - 量化回测平台

基于 LLM 的股票交易回测平台，支持多个大语言模型（Qwen、DeepSeek、Kimi、ChatGLM）进行自动化交易决策。

## 功能特性

- 📊 **数值回测模式**：快速回测，生成收益曲线和统计数据
- 💬 **NLP 回测模式**：记录每个模型的自然语言决策过程，便于分析 AI 的思考过程
- 📈 **可视化界面**：基于 Streamlit 的 Web 界面，实时查看回测进度和结果
- 🔄 **断点续传**：支持从 checkpoint 恢复长时间回测
- 📉 **技术指标**：自动计算每日技术指标，丰富决策信息

## 快速开始

### 1. 环境准备

```bash
# 创建 conda 环境（推荐）
conda create -n alpha_arena_env python=3.11
conda activate alpha_arena_env

# 或使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 安装依赖

```bash
cd quant_unstructure
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件（项目根目录），添加你的 API 密钥：

```env
# Qwen API
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://api.example.com/v1

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Kimi API
KIMI_API_KEY=your_kimi_api_key
KIMI_BASE_URL=https://api.moonshot.cn/v1

# ChatGLM API
CHATGLM_API_KEY=your_chatglm_api_key
```

### 4. 准备股票数据

确保 `original_data/` 目录下有道琼斯 30 成分股的 CSV 数据文件，格式：
- 文件名：股票代码.csv（如 `AAPL.csv`）
- 必需列：`Date`, `Open`, `High`, `Low`, `Close`, `Volume`

如果没有数据，可以使用 `utils/fetch_dow30_data.py` 脚本获取。

### 5. 运行 Streamlit 应用

```bash
cd quant_unstructure
streamlit run streamlit_app.py
```

浏览器会自动打开 `http://localhost:8501`

## 使用指南

### 启动回测

1. **选择回测模式**
   - **数值回测**：快速回测，只保存数值结果
   - **NLP 回测**：同时保存自然语言决策日志

2. **配置参数**
   - **日期范围**：选择回测的开始和结束日期
   - **初始资金**：设置初始现金（默认 100,000）
   - **历史数据窗口**：用于计算技术指标的历史天数（默认 30 天）
   - **选择模型**：勾选要测试的 LLM 模型

3. **断点续传**（可选）
   - 勾选 "Resume from Checkpoint" 可以从上次中断的地方继续
   - 系统会自动检测可用的 checkpoint

4. **开始回测**
   - 点击 "Start Backtest" 按钮
   - 实时查看进度和预计剩余时间

### 查看结果

- **收益曲线**：可视化每个模型的累计收益率
- **统计数据**：查看总收益率、最大回撤等指标
- **NLP 日志**（仅 NLP 模式）：查看每个模型在每日的决策理由和账户状态

### 结果文件

- **数值结果**：`results/{model_name}.csv`
- **NLP 日志**：`results_nlp/{model_name}_nlp.jsonl`
- **Checkpoint**：`ckpt/AccountInfoLLMs/` 和 `ckpt/ProfitInfoLLMs/`

## 命令行回测（可选）

如果不使用 Streamlit 界面，也可以直接运行：

```bash
# 数值回测
python main.py

# NLP 回测
python main_nlp.py
```

需要在代码中修改配置参数。

## 项目结构

```
quant_unstructure/
├── streamlit_app.py      # Streamlit Web 应用
├── main.py               # 数值回测主程序
├── main_nlp.py           # NLP 回测主程序
├── backend/              # 后端 API（可选）
├── utils/                # 工具函数
│   ├── get_stocks_info.py    # 股票数据获取
│   ├── process_output.py     # LLM 输出处理
│   ├── save_result.py        # 结果保存
│   └── indicators_daily.py   # 技术指标计算
├── llm/                  # LLM API 客户端
├── results/              # 数值回测结果
├── results_nlp/          # NLP 日志
├── ckpt/                 # Checkpoint 文件
├── original_data/        # 原始股票数据
└── requirements.txt      # Python 依赖
```

## 常见问题

### Q: 如何获取股票数据？
A: 使用 `utils/fetch_dow30_data.py` 脚本，或手动下载 CSV 文件到 `original_data/` 目录。

### Q: 回测中断了怎么办？
A: 勾选 "Resume from Checkpoint" 选项，系统会自动从最近的 checkpoint 恢复。

### Q: NLP 日志文件找不到？
A: 确保选择了 "NLP Backtest" 模式，并且回测已完成。检查 `results_nlp/` 目录。

### Q: API 调用失败？
A: 检查 `.env` 文件中的 API 密钥是否正确，以及网络连接是否正常。

## 技术栈

- **前端**：Streamlit
- **可视化**：Plotly
- **数据处理**：Pandas, NumPy
- **LLM API**：OpenAI SDK, ZhipuAI SDK
- **数据源**：yfinance（可选）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
