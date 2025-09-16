# 量化金融分析工具库

一个用于金融数据分析和量化研究的Python工具库，专注于SEC文件处理、财务数据分析和技术指标计算。

## 功能特性

- 📊 SEC文件下载和解析
- 📈 财务数据分析（MDNA处理）
- 🤖 情感分析工具
- 🔢 技术指标计算
- 📋 数据清洗和预处理

## 项目结构

```
quant/
├── clean_financial_reports.py    # 财务报告清洗工具
├── download_dogs_mdna.py        # 道琼斯30成分股MDNA下载
├── financial_sentiment_analyzer.py # 金融情感分析
├── llm_provider.py              # LLM服务提供商接口
├── sec_test.py                  # SEC API测试
├── utils/                       # 工具函数
├── backtrader/                  # 回测框架相关
└── quant_rl/                   # 量化强化学习
```

## 安装要求

```bash
pip install -r requirements.txt
```

## 使用方法

1. 下载SEC文件：
```python
python download_dogs_mdna.py
```

2. 处理财务数据：
```python
python process_jpm_mdna.py
```

3. 运行情感分析：
```python
python financial_sentiment_analyzer.py
```

## 数据说明

项目使用SEC EDGAR API获取上市公司财务数据，主要处理10-Q和10-K文件中的Management Discussion & Analysis (MDNA)部分。

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License

## 免责声明

本项目仅用于教育和研究目的，不构成投资建议。使用者应自行承担风险。