# Project Guide: MD&A Extraction & Cleaning → Sentiment Factors → Backtesting and Plots

This repository implements an end-to-end workflow to:

- Download and extract MD&A sections from SEC filings
- Clean and normalize MD&A text
- Run multi-dimensional financial sentiment analysis to produce sentiment factors
- Backtest trading strategies based on those factors
- Generate result plots and comparison tables

- Data acquisition and cleaning: `sec_processing/`, `data/`
- Sentiment analysis and factors: `ai_analysis/`
- Backtesting and plotting: `backtesting/`

## 1. Environment Setup

Recommended: Python 3.10+ and a virtual environment.

```bash
# At repository root
python -m venv .venv && source .venv/bin/activate
pip install -U pip

# Install backtesting/plotting dependencies
pip install -r backtesting/requirements.txt
```

Notes:
- HF mirror environment variables are configured inside `backtesting/run.py`.
- `.gitignore` excludes large datasets and generated artifacts; only whitelisted result folders are committed.

## 2. MD&A Download and Extraction

Download MD&A sections for the Dogs of the Dow 30:

```bash
python sec_processing/download_dogs_mdna.py
```

Main outputs:
- `data/dogs_of_30_mdna/`: raw MD&A text organized by company/filing
- `data/filing_urls.txt`: links to 10-K/10-Q filings used for downloads
- (Optional) If you produce markdown-cleaned texts: `data/mdna_markdowns/`

Single-company processing examples (as references):
- `sec_processing/process_intc_mdna.py`
- `sec_processing/process_jpm_mdna.py`

## 3. Text Cleaning and Structuring

Typical cleaning includes section segmentation, noise removal, encoding normalization, and format unification. Directory conventions:
- Raw/intermediate: `data/dogs_of_30_mdna/`, `data/mdna_markdowns/`
- Aggregated structured data (if generated): `data/processed_financial_data.json`

To re-run/extend cleaning, follow patterns in scripts under `sec_processing/`.

## 4. Sentiment Analysis → Factor Generation

Run multi-dimensional financial sentiment analysis to produce factors:

```bash
python ai_analysis/financial_sentiment_analyzer.py
```

Key outputs (paths defined inside the script):
- `data/financial_sentiment_analysis.json`: per-filing or per-period sentiment results
- `data/sentiment_factors.csv`: aggregated sentiment factors (used by backtesting)

Note: Prompt templates are embedded in code; `prompt/prompt.json` is currently unused. You may delete it or keep it as a placeholder for future externalization.

## 5. Backtesting with Sentiment Factors

Run the three-strategy backtest (Original Sentiment, Top-K Sentiment, Buy&Hold):

```bash
python backtesting/run.py
```

Defaults in `backtesting/run.py`:
- Data dir: `/root/quant/data/dogs_of_30_mdna`
- Output dir: `/root/quant/backtesting/results`
- Period: 2020-01-01 to 2024-12-31
- Analyzer: `fingpt` (switch to `deepseek` to use DeepSeek)

Backtest outputs (CSV):
- `backtesting/results/original_strategy_performance.csv`
- `backtesting/results/topk_strategy_performance.csv`
- `backtesting/results/buy_hold_performance.csv`

### 5.1 FinGPT vs DeepSeek Comparison (Optional)

Run both analyzers and generate comparison artifacts:

```bash
python backtesting/run_comparison.py
```

Outputs:
- FinGPT results: `backtesting/results_fingpt/` (committed)
- DeepSeek results: `backtesting/results_deepseek/` (ignored)
- Comparison: `backtesting/results_comparison/` (committed)
  - `comparison_data.csv`
  - `metrics_comparison.csv`
  - `finGPT_vs_deepseek_comparison.png`

## 6. Plot Generation (Three Strategies)

Generate fixed-style plots from the three-strategy results:

```bash
python backtesting/generate_plots_fixed.py
```

Outputs:
- `backtesting/results/cumulative_returns_three_strategies.png`
- `backtesting/results/quarterly_returns_three_strategies.png`
- `backtesting/results/metrics_comparison_three_strategies.png`

## 7. Directory and Commit Policy

- Committed:
  - `backtesting/results_fingpt/**`
  - `backtesting/results_comparison/**`
- Ignored (not committed):
  - `backtesting/results_deepseek/**`
  - Generic large data/intermediate artifacts (e.g., `data/`, `outputs/`) and common large file types unless explicitly whitelisted

To commit an additional results folder, add an exception rule (e.g., `!backtesting/your_results_dir/**`) in `.gitignore`.

## 8. Quickstart (Command Summary)

```bash
# 1) Download MD&A
python sec_processing/download_dogs_mdna.py

# 2) Generate sentiment factors
python ai_analysis/financial_sentiment_analyzer.py

# 3) Run backtest (FinGPT)
python backtesting/run.py

# 4) Create three-strategy plots from CSVs
python backtesting/generate_plots_fixed.py

# Optional: end-to-end comparison (FinGPT vs DeepSeek)
python backtesting/run_comparison.py
```

## 9. Troubleshooting

- Backtest errors:
  - Ensure dependencies are installed: `pip install -r backtesting/requirements.txt`
  - Ensure data directory exists: `/root/quant/data/dogs_of_30_mdna/`
  - Ensure sufficient disk space and memory
- Plotting errors:
  - Verify required CSVs exist in `backtesting/results/` or `backtesting/results_fingpt/`

— If you plan to publish more result folders, update exceptions in `.gitignore` accordingly.
