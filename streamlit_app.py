"""
Alpha Arena Backtesting Platform (Streamlit)

Features:
- Configure backtest parameters (dates, models, initial cash, etc.)
- Run backtests asynchronously with real-time progress
- Visualize profit curves using Plotly
- View NLP backtest natural language decision logs

Usage:
1. Ensure you're in alpha_arena_env environment with dependencies installed:
   pip install streamlit plotly
2. Run from quant_unstructure directory:
   cd quant_unstructure
   streamlit run streamlit_app.py
"""

import sys
import os
import json
import threading
import time
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Ensure we can import existing backtest logic
# BASE_DIR is the quant_unstructure directory (where this file is located)
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 导入回测相关模块
from backend.core.models import BacktestConfig, BacktestStatus
from backend.core.backtest_engine import BacktestEngine
from utils.get_stocks_info import get_stocks_info
from utils.save_result import save_all_llm_results

# 导入数值回测
from main import (
    LLMs as NUMERIC_LLMs,
    AccountInfoLLMs as NUMERIC_AccountInfoLLMs,
    ProfitInfoLLMs as NUMERIC_ProfitInfoLLMs,
    initialize_llm_info,
    initialize_profit_info,
    market_trading_parallel,
)

# 导入 NLP 回测
from main_nlp import (
    LLMs as NLP_LLMs,
    AccountInfoLLMs as NLP_AccountInfoLLMs,
    ProfitInfoLLMs as NLP_ProfitInfoLLMs,
    initialize_llm_info_nlp,
    initialize_profit_info_nlp,
    market_trading_nlp,
)

# Page configuration
st.set_page_config(
    page_title="Alpha Arena Backtesting Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 模型选项
MODEL_OPTIONS = {
    "qwen": "Qwen",
    "deepseek": "DeepSeek",
    "kimi": "Kimi",
    "chatglm": "ChatGLM",
}

# 初始化 session_state
if "backtest_status" not in st.session_state:
    st.session_state.backtest_status = None
if "backtest_thread" not in st.session_state:
    st.session_state.backtest_thread = None
if "backtest_progress" not in st.session_state:
    st.session_state.backtest_progress = {
        "current_day": 0,
        "total_days": 0,
        "models_status": {},
        "message": "",
        "start_time": None,
    }
if "backtest_result" not in st.session_state:
    st.session_state.backtest_result = None
if "backtest_error" not in st.session_state:
    st.session_state.backtest_error = None


def run_numeric_backtest(
    config: BacktestConfig,
    progress_dict: Dict[str, Any],
    result_dict: Dict[str, Any],
    error_dict: Dict[str, Any],
    resume_from_checkpoint: bool = False,
    model_resume_dates: Optional[Dict[str, str]] = None,
):
    """Run numeric backtest (background thread)"""
    try:
        progress_dict["message"] = "Initializing..."
        progress_dict["start_time"] = time.time()
        
        # Prepare models
        selected_llms = {
            model: NUMERIC_LLMs[model]
            for model in config.models
            if model in NUMERIC_LLMs and NUMERIC_LLMs[model] is not None
        }
        
        if not selected_llms:
            raise ValueError("No available models")
        
        # Initialize account info
        if not resume_from_checkpoint:
            NUMERIC_AccountInfoLLMs.clear()
            NUMERIC_ProfitInfoLLMs.clear()
        
        NUMERIC_AccountInfoLLMs.update(
            initialize_llm_info(
                selected_llms,
                config.initial_cash,
                AccountInfoLLMs=NUMERIC_AccountInfoLLMs,
                resume_from_ckpt=resume_from_checkpoint,
                ckpt_dir=str(BASE_DIR / "ckpt" / "AccountInfoLLMs"),
            )
        )
        NUMERIC_ProfitInfoLLMs.update(
            initialize_profit_info(
                ProfitInfoLLMs=NUMERIC_ProfitInfoLLMs,
                resume_from_ckpt=resume_from_checkpoint,
                ckpt_dir=str(BASE_DIR / "ckpt" / "ProfitInfoLLMs"),
            )
            or {}
        )
        
        # Get stock data
        progress_dict["message"] = "Loading stock data..."
        stocks_dict, all_stocks_names = get_stocks_info(
            stocks_root=str(BASE_DIR / "original_data"),
            start_date=config.start_date,
            end_date=config.end_date,
        )
        
        total_days = len([d for d in stocks_dict.keys() if isinstance(d, str)])
        # Subtract history days since we skip the first 'history' days
        progress_dict["total_days"] = max(0, total_days - config.history)
        
        # If resuming from checkpoint, calculate how many days are already processed
        if resume_from_checkpoint:
            from utils.save_result import find_latest_ckpt_file
            profit_ckpt_dir = BASE_DIR / "ckpt" / "ProfitInfoLLMs"
            latest_profit_ckpt = find_latest_ckpt_file(str(profit_ckpt_dir))
            if latest_profit_ckpt:
                import re
                match = re.search(r"/(\d+)\.json$", latest_profit_ckpt)
                if match:
                    ckpt_day = int(match.group(1))
                    # ckpt_day is 0-indexed, but we need to account for history offset
                    progress_dict["current_day"] = max(0, ckpt_day - config.history)
                    progress_dict["message"] = f"Resuming from checkpoint at day {ckpt_day}"
                    print(f"[Numeric Backtest] Resuming from checkpoint: day {ckpt_day}")
        
        # Clear checkpoints only if not resuming
        if not resume_from_checkpoint:
            ckpt_dir = BASE_DIR / "ckpt" / "AccountInfoLLMs"
            if ckpt_dir.exists():
                for f in ckpt_dir.glob("*.json"):
                    f.unlink()
            ckpt_dir = BASE_DIR / "ckpt" / "ProfitInfoLLMs"
            if ckpt_dir.exists():
                for f in ckpt_dir.glob("*.json"):
                    f.unlink()
        
        # Run backtest
        progress_dict["message"] = "Running backtest..."
        
        # Temporarily set global LLMs
        import main as main_module
        original_llms = main_module.LLMs.copy()
        main_module.LLMs = selected_llms
        
        try:
            # Define progress callback to update progress_dict
            def update_progress(current_day, total_days, date):
                progress_dict["current_day"] = current_day
                progress_dict["message"] = f"Processing day {current_day}/{total_days}: {date}"
            
            market_trading_parallel(
                NUMERIC_AccountInfoLLMs,
                NUMERIC_ProfitInfoLLMs,
                stocks_dict,
                history=config.history,
                debug=config.debug,
                max_workers=len(selected_llms),
                progress_callback=update_progress,
            )
        finally:
            # Restore original LLMs
            main_module.LLMs = original_llms
        
        # Collect result files
        result_files = []
        for model_name in selected_llms.keys():
            result_file = BASE_DIR / "results" / f"{model_name}.csv"
            if result_file.exists():
                result_files.append(str(result_file))
        
        result_dict["status"] = "completed"
        result_dict["result_files"] = result_files
        result_dict["models"] = list(selected_llms.keys())
        progress_dict["current_day"] = total_days
        progress_dict["message"] = "Backtest completed!"
        # Don't modify session_state in background thread, let main thread check result_dict
        
    except Exception as e:
        error_dict["error"] = str(e)
        progress_dict["message"] = f"Backtest failed: {str(e)}"


def run_nlp_backtest(
    config: BacktestConfig,
    progress_dict: Dict[str, Any],
    result_dict: Dict[str, Any],
    error_dict: Dict[str, Any],
    resume_from_checkpoint: bool = False,
    model_resume_dates: Optional[Dict[str, str]] = None,
):
    """Run NLP backtest (background thread)"""
    import traceback
    try:
        progress_dict["message"] = "Initializing NLP backtest..."
        progress_dict["start_time"] = time.time()
        print(f"[NLP Backtest] Starting, config: {config}")
        
        # Prepare models
        selected_llms = {
            model: NLP_LLMs[model]
            for model in config.models
            if model in NLP_LLMs and NLP_LLMs[model] is not None
        }
        
        if not selected_llms:
            raise ValueError("No available models")
        
        # Initialize account info
        if not resume_from_checkpoint:
            NLP_AccountInfoLLMs.clear()
            NLP_ProfitInfoLLMs.clear()
        else:
            # If resuming with specific dates, load account state from NLP logs
            if model_resume_dates:
                nlp_dir = BASE_DIR / "results_nlp"
                for model, resume_date in model_resume_dates.items():
                    if resume_date and model in selected_llms:
                        nlp_file = nlp_dir / f"{model}_nlp.jsonl"
                        if nlp_file.exists():
                            try:
                                # Find the record for the resume date
                                with open(nlp_file, "r", encoding="utf-8") as f:
                                    for line in f:
                                        if line.strip():
                                            record = json.loads(line)
                                            if record.get("date") == resume_date and "account_after" in record:
                                                # Load account state from this date
                                                NLP_AccountInfoLLMs[model] = record["account_after"].copy()
                                                print(f"[NLP Backtest] Loaded {model} account state from {resume_date}")
                                                break
                            except Exception as e:
                                print(f"[NLP Backtest] Error loading account state for {model}: {e}")
        
        NLP_AccountInfoLLMs.update(
            initialize_llm_info_nlp(
                selected_llms,
                config.initial_cash,
                AccountInfoLLMs=NLP_AccountInfoLLMs,
                resume_from_ckpt=resume_from_checkpoint,
                ckpt_dir=str(BASE_DIR / "ckpt" / "nlp" / "AccountInfoLLMs"),
            )
        )
        NLP_ProfitInfoLLMs.update(
            initialize_profit_info_nlp(
                ProfitInfoLLMs=NLP_ProfitInfoLLMs,
                resume_from_ckpt=resume_from_checkpoint,
                ckpt_dir=str(BASE_DIR / "ckpt" / "nlp" / "ProfitInfoLLMs"),
            )
            or {}
        )
        
        # Mark dates as processed if resuming from specific dates
        # Mark all dates up to and INCLUDING resume_date as processed
        # This way, when start_date is set to resume_date + 1 day, we skip all dates up to resume_date
        if resume_from_checkpoint and model_resume_dates:
            for model, resume_date in model_resume_dates.items():
                if resume_date and model in NLP_ProfitInfoLLMs:
                    # Mark all dates up to and including resume_date as processed
                    # Since start_date will be resume_date + 1, we want to skip resume_date and all before it
                    nlp_file = BASE_DIR / "results_nlp" / f"{model}_nlp.jsonl"
                    if nlp_file.exists():
                        dates = extract_dates_from_nlp_log(str(nlp_file))
                        for date_str in dates:
                            if date_str <= resume_date:  # Mark dates up to and including resume_date
                                # Mark this date as already processed
                                if model not in NLP_ProfitInfoLLMs:
                                    NLP_ProfitInfoLLMs[model] = {}
                                if date_str not in NLP_ProfitInfoLLMs[model]:
                                    NLP_ProfitInfoLLMs[model][date_str] = {}
                                    print(f"[NLP Backtest] Marked {model} date {date_str} as processed (up to resume date {resume_date})")
        
        # Get stock data
        progress_dict["message"] = "Loading stock data..."
        stocks_dict, all_stocks_names = get_stocks_info(
            stocks_root=str(BASE_DIR / "original_data"),
            start_date=config.start_date,
            end_date=config.end_date,
        )
        
        total_days = len([d for d in stocks_dict.keys() if isinstance(d, str)])
        # Subtract history days since we skip the first 'history' days
        progress_dict["total_days"] = max(0, total_days - config.history)
        
        # If resuming from checkpoint, calculate how many days are already processed
        if resume_from_checkpoint:
            from utils.save_result import find_latest_ckpt_file
            profit_ckpt_dir = BASE_DIR / "ckpt" / "nlp" / "ProfitInfoLLMs"
            latest_profit_ckpt = find_latest_ckpt_file(str(profit_ckpt_dir))
            if latest_profit_ckpt:
                import re
                match = re.search(r"/(\d+)\.json$", latest_profit_ckpt)
                if match:
                    ckpt_day = int(match.group(1))
                    # ckpt_day is 0-indexed, but we need to account for history offset
                    progress_dict["current_day"] = max(0, ckpt_day - config.history)
                    progress_dict["message"] = f"Resuming from checkpoint at day {ckpt_day}"
                    print(f"[NLP Backtest] Resuming from checkpoint: day {ckpt_day}")
        
        # Clear checkpoints and NLP logs only if not resuming
        if not resume_from_checkpoint:
            ckpt_dir = BASE_DIR / "ckpt" / "nlp" / "AccountInfoLLMs"
            if ckpt_dir.exists():
                for f in ckpt_dir.glob("*.json"):
                    f.unlink()
            ckpt_dir = BASE_DIR / "ckpt" / "nlp" / "ProfitInfoLLMs"
            if ckpt_dir.exists():
                for f in ckpt_dir.glob("*.json"):
                    f.unlink()
            
            # Clear NLP log files only for selected models (only if starting fresh, not when resuming from checkpoint)
            # When resuming, we want to keep existing logs and append new ones
            # Different AI models should keep their own jsonl files and not overwrite each other
            if not resume_from_checkpoint:
                nlp_dir = BASE_DIR / "results_nlp"
                if nlp_dir.exists():
                    # Only delete jsonl files for selected models, keep other models' files
                    for model in selected_llms.keys():
                        nlp_file = nlp_dir / f"{model}_nlp.jsonl"
                        if nlp_file.exists():
                            nlp_file.unlink()
                            print(f"[NLP Backtest] Cleared NLP log file for {model}: {nlp_file}")
        
        # Run NLP backtest
        progress_dict["message"] = "Running NLP backtest..."
        print(f"[NLP Backtest] Starting market_trading_nlp, total trading days: {total_days}")
        
        # Temporarily set global LLMs and save path
        import main_nlp as nlp_module
        original_llms = nlp_module.LLMs.copy()
        original_save_root = nlp_module.SAVE_ROOT_NLP
        nlp_module.LLMs = selected_llms
        # Ensure using absolute path from project root for NLP logs
        nlp_module.SAVE_ROOT_NLP = str(BASE_DIR / "results_nlp")
        # Ensure directory exists
        os.makedirs(nlp_module.SAVE_ROOT_NLP, exist_ok=True)
        print(f"[NLP Backtest] NLP log save path: {nlp_module.SAVE_ROOT_NLP}")
        print(f"[NLP Backtest] Path exists: {os.path.exists(nlp_module.SAVE_ROOT_NLP)}")
        
        try:
            # Define progress callback to update progress_dict
            def update_progress(current_day, total_days, date):
                progress_dict["current_day"] = current_day
                progress_dict["message"] = f"Processing day {current_day}/{total_days}: {date}"
            
            market_trading_nlp(
                NLP_AccountInfoLLMs,
                NLP_ProfitInfoLLMs,
                stocks_dict,
                history=config.history,
                debug=config.debug,
                progress_callback=update_progress,
            )
            print(f"[NLP Backtest] market_trading_nlp execution completed")
        except Exception as e:
            print(f"[NLP Backtest] market_trading_nlp execution error: {e}")
            print(traceback.format_exc())
            raise
        finally:
            # Restore original LLMs and save path
            nlp_module.LLMs = original_llms
            nlp_module.SAVE_ROOT_NLP = original_save_root
        
        # Collect result files
        result_files = []
        nlp_files = []
        nlp_dir = BASE_DIR / "results_nlp"
        
        print(f"[NLP Backtest] Checking result files, BASE_DIR: {BASE_DIR}")
        print(f"[NLP Backtest] NLP directory: {nlp_dir}, exists: {nlp_dir.exists()}")
        if nlp_dir.exists():
            all_nlp_files = list(nlp_dir.glob("*.jsonl"))
            print(f"[NLP Backtest] Found NLP files: {[str(f) for f in all_nlp_files]}")
        
        for model_name in selected_llms.keys():
            result_file = BASE_DIR / "results" / f"{model_name}.csv"
            nlp_file = BASE_DIR / "results_nlp" / f"{model_name}_nlp.jsonl"
            
            print(f"[NLP Backtest] Checking {model_name}: CSV={result_file.exists()}, NLP={nlp_file.exists()}")
            if result_file.exists():
                result_files.append(str(result_file))
            if nlp_file.exists():
                nlp_files.append(str(nlp_file))
            else:
                # If file doesn't exist, list all files in directory
                if nlp_dir.exists():
                    files_in_dir = list(nlp_dir.glob("*"))
                    print(f"[NLP Backtest] {model_name} NLP file not found, files in directory: {[str(f) for f in files_in_dir]}")
        
        # Verify result files exist
        if not result_files:
            raise ValueError("Backtest completed but no result files generated, please check if backtest actually executed")
        
        # If NLP files don't exist, warn but don't throw error
        if not nlp_files:
            print(f"[NLP Backtest] Warning: No NLP log files found!")
            print(f"[NLP Backtest] Please check if market_trading_nlp actually executed save_llm_raw_output")
        
        result_dict["status"] = "completed"
        result_dict["result_files"] = result_files
        result_dict["nlp_files"] = nlp_files
        result_dict["models"] = list(selected_llms.keys())
        progress_dict["current_day"] = total_days
        progress_dict["message"] = "NLP backtest completed!"
        print(f"[NLP Backtest] Backtest completed, result files: {result_files}, NLP files: {nlp_files}")
        # Don't modify session_state in background thread, let main thread check result_dict
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
        error_dict["error"] = error_msg
        progress_dict["message"] = f"NLP backtest failed: {str(e)}"
        print(f"[NLP Backtest] Backtest failed: {error_msg}")


def load_results(result_files: List[str]) -> Dict[str, pd.DataFrame]:
    """Load backtest result CSV files"""
    dfs = {}
    for file_path in result_files:
        if os.path.exists(file_path):
            model_name = Path(file_path).stem
            df = pd.read_csv(file_path)
            df["Date"] = pd.to_datetime(df["Date"])
            dfs[model_name] = df
    return dfs


def extract_dates_from_nlp_log(nlp_file: str) -> List[str]:
    """Extract all dates from an NLP log file"""
    dates = []
    if not os.path.exists(nlp_file):
        return dates
    try:
        with open(nlp_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if "date" in record:
                            dates.append(record["date"])
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error reading NLP log {nlp_file}: {e}")
    return sorted(set(dates))  # Return unique sorted dates


def get_model_checkpoint_dates(selected_models: List[str], backtest_mode: str) -> Dict[str, List[str]]:
    """Get available checkpoint dates for each selected model from NLP logs"""
    model_dates = {}
    nlp_dir = BASE_DIR / "results_nlp"
    
    for model in selected_models:
        if backtest_mode == "NLP Backtest":
            nlp_file = nlp_dir / f"{model}_nlp.jsonl"
            dates = extract_dates_from_nlp_log(str(nlp_file))
            if dates:
                model_dates[model] = dates
        else:
            # For numeric backtest, check checkpoint files
            ckpt_dir = BASE_DIR / "ckpt" / "AccountInfoLLMs"
            if ckpt_dir.exists():
                # Try to get dates from checkpoint or profit files
                profit_ckpt_dir = BASE_DIR / "ckpt" / "ProfitInfoLLMs"
                dates = []
                if profit_ckpt_dir.exists():
                    from utils.save_result import load_info_dict
                    for ckpt_file in sorted(profit_ckpt_dir.glob(f"{model}_*.json")):
                        try:
                            data = load_info_dict(str(ckpt_file))
                            if data:
                                # Extract dates from profit info
                                dates.extend([k for k in data.keys() if isinstance(k, str) and len(k) == 10])
                        except:
                            pass
                if dates:
                    model_dates[model] = sorted(set(dates))
    
    return model_dates


def load_nlp_logs(nlp_files: List[str]) -> Dict[str, List[Dict]]:
    """Load NLP log files"""
    logs = {}
    for file_path in nlp_files:
        if os.path.exists(file_path):
            model_name = Path(file_path).stem.replace("_nlp", "")
            model_logs = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            model_logs.append(record)
                        except json.JSONDecodeError:
                            continue
            logs[model_name] = model_logs
    return logs


def plot_profit_curves(dfs: Dict[str, pd.DataFrame]) -> go.Figure:
    """Plot profit curves"""
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Account Value Over Time", "Return Percentage Over Time"),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
    )
    
    colors = px.colors.qualitative.Set2
    
    for idx, (model, df) in enumerate(dfs.items()):
        color = colors[idx % len(colors)]
        model_label = MODEL_OPTIONS.get(model, model)
        
        # Account value curve
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["AccountValue"],
                mode="lines",
                name=f"{model_label} - Account Value",
                line=dict(color=color, width=2),
                legendgroup=model,
            ),
            row=1,
            col=1,
        )
        
        # Return percentage curve
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["ReturnPercent"] * 100,
                mode="lines",
                name=f"{model_label} - Return (%)",
                line=dict(color=color, width=2, dash="dash"),
                legendgroup=model,
                showlegend=False,
            ),
            row=2,
            col=1,
        )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Account Value ($)", row=1, col=1)
    fig.update_yaxes(title_text="Return (%)", row=2, col=1)
    
    fig.update_layout(
        height=700,
        title_text="Backtest Results Comparison",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    
    return fig


def main():
    """Main function"""
    # Title
    st.title("📈 Alpha Arena Backtesting Platform")
    st.markdown("---")
    
    # Sidebar: Backtest configuration
    with st.sidebar:
        st.header("⚙️ Backtest Configuration")
        
        # Backtest mode selection
        backtest_mode = st.radio(
            "Backtest Mode",
            ["Numeric Backtest", "NLP Backtest"],
            help="Numeric Backtest: Save numeric results only; NLP Backtest: Also save natural language decision logs",
        )
        
        # Date selection
        today = date.today()
        col1, col2 = st.columns(2)
        with col1:
            # Initialize start_date, will be updated if resuming from checkpoint
            default_start_date = date(2025, 1, 1)
            if 'resume_start_date' in st.session_state:
                default_start_date = st.session_state.resume_start_date
            
            start_date = st.date_input(
                "Start Date",
                value=default_start_date,
                min_value=date(2020, 1, 1),
                max_value=today,
                key="start_date_input",
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=today,  # Default to today instead of future date
                min_value=date(2020, 1, 1),
                max_value=today,
            )
        
        # Initial cash
        initial_cash = st.number_input(
            "Initial Cash ($)",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=10000.0,
        )
        
        # Model selection
        selected_models = st.multiselect(
            "Select Models",
            options=list(MODEL_OPTIONS.keys()),
            default=list(MODEL_OPTIONS.keys()),
            format_func=lambda x: MODEL_OPTIONS[x],
        )
        
        # History window
        history = st.number_input(
            "History Window",
            min_value=1,
            max_value=30,
            value=10,
            help="Number of historical trading days for calculating technical indicators",
        )
        
        st.markdown("---")
        
        # Resume from checkpoint option
        resume_from_checkpoint = st.checkbox(
            "Resume from Checkpoint",
            value=False,
            help="If enabled, continue from a saved checkpoint. You can select which date to resume from for each model."
        )
        
        # Update session state if user manually changes start_date (but only if not resuming)
        # This needs to be after resume_from_checkpoint is defined
        if not resume_from_checkpoint and 'start_date_input' in st.session_state:
            current_start_date = st.session_state.start_date_input
            if 'resume_start_date' not in st.session_state or st.session_state.resume_start_date != current_start_date:
                st.session_state.resume_start_date = current_start_date
        
        # Model-specific resume date selection
        model_resume_dates = {}
        earliest_resume_date = None
        
        if resume_from_checkpoint and selected_models:
            st.markdown("**📅 Select Resume Date for Each Model:**")
            
            # Get available dates for each model
            model_checkpoint_dates = get_model_checkpoint_dates(selected_models, backtest_mode)
            
            # Debug info
            if not model_checkpoint_dates:
                nlp_dir = BASE_DIR / "results_nlp"
                st.warning(f"⚠️ No checkpoint dates found. Debug info:")
                st.caption(f"  - NLP directory: {nlp_dir} (exists: {nlp_dir.exists()})")
                if nlp_dir.exists():
                    all_files = list(nlp_dir.glob("*.jsonl"))
                    st.caption(f"  - Found {len(all_files)} jsonl files: {[f.name for f in all_files]}")
                st.caption(f"  - Selected models: {selected_models}")
                st.caption(f"  - Backtest mode: {backtest_mode}")
            
            if model_checkpoint_dates:
                for model in selected_models:
                    model_name = MODEL_OPTIONS.get(model, model)
                    available_dates = model_checkpoint_dates.get(model, [])
                    
                    if available_dates:
                        # Show account state from the last date
                        last_date = available_dates[-1]
                        nlp_file = BASE_DIR / "results_nlp" / f"{model}_nlp.jsonl"
                        
                        # Try to load account state from NLP log
                        account_info = None
                        if nlp_file.exists() and backtest_mode == "NLP Backtest":
                            try:
                                with open(nlp_file, "r", encoding="utf-8") as f:
                                    for line in f:
                                        if line.strip():
                                            record = json.loads(line)
                                            if record.get("date") == last_date and "account_after" in record:
                                                account_info = record["account_after"]
                                                break
                            except:
                                pass
                        
                        # Display model info
                        with st.expander(f"📊 {model_name} - Last processed: {last_date}", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                selected_date = st.selectbox(
                                    f"Resume from date:",
                                    options=available_dates,
                                    index=len(available_dates) - 1,  # Default to last date
                                    key=f"resume_date_{model}",
                                    help=f"Select which date to resume from. Start date will be set to the day after this date."
                                )
                                model_resume_dates[model] = selected_date
                                
                                # Track earliest resume date to update start_date
                                if selected_date:
                                    try:
                                        resume_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
                                        if earliest_resume_date is None or resume_date_obj < earliest_resume_date:
                                            earliest_resume_date = resume_date_obj
                                    except:
                                        pass
                            
                            with col2:
                                if account_info:
                                    st.metric("Account Value", f"${account_info.get('currentAccountValue', 0):,.2f}")
                                    st.metric("Available Cash", f"${account_info.get('availableCash', 0):,.2f}")
                                    positions = account_info.get('positions', {})
                                    if positions:
                                        st.caption(f"Holdings: {', '.join(positions.keys())}")
                                    else:
                                        st.caption("No positions")
                                else:
                                    st.info("Account info not available")
                    else:
                        st.warning(f"⚠️ {model_name}: No checkpoint dates found. Will start from beginning.")
                        model_resume_dates[model] = None
            else:
                st.warning("⚠️ No checkpoint dates found for selected models. Will start from beginning.")
        
        # Auto-update start_date based on selected resume date
        if resume_from_checkpoint and earliest_resume_date:
            from datetime import timedelta
            # Set start_date to the day after the earliest resume date
            new_start_date = earliest_resume_date + timedelta(days=1)
            if new_start_date <= end_date:
                # Update start_date in session state (but don't modify widget state directly)
                if 'resume_start_date' not in st.session_state or st.session_state.resume_start_date != new_start_date:
                    st.session_state.resume_start_date = new_start_date
                    st.info(f"📅 Start date automatically set to {new_start_date.strftime('%Y-%m-%d')} (day after resume date {earliest_resume_date.strftime('%Y-%m-%d')})")
                    st.rerun()  # Rerun to update the UI with new date
                # Use the updated start_date
                start_date = st.session_state.resume_start_date
            else:
                st.warning(f"⚠️ Calculated start date {new_start_date} is after end date. Please adjust dates manually.")
        
        # Show checkpoint status if available (legacy display)
        if resume_from_checkpoint:
            ckpt_dir = BASE_DIR / "ckpt" / ("nlp" if backtest_mode == "NLP Backtest" else "") / "AccountInfoLLMs"
            if backtest_mode == "NLP Backtest":
                ckpt_dir = BASE_DIR / "ckpt" / "nlp" / "AccountInfoLLMs"
            else:
                ckpt_dir = BASE_DIR / "ckpt" / "AccountInfoLLMs"
            
            from utils.save_result import find_latest_ckpt_file
            latest_ckpt = find_latest_ckpt_file(str(ckpt_dir))
            
            if latest_ckpt:
                # Extract checkpoint day number from filename
                import re
                match = re.search(r"/(\d+)\.json$", latest_ckpt)
                if match:
                    ckpt_day = int(match.group(1))
                    st.info(f"📌 Found checkpoint at day {ckpt_day}")
                    
                    # Try to load and show checkpoint info
                    try:
                        from utils.save_result import load_info_dict
                        ckpt_data = load_info_dict(latest_ckpt)
                        if ckpt_data:
                            # Get the last processed date from ProfitInfoLLMs
                            profit_ckpt_dir = BASE_DIR / "ckpt" / ("nlp" if backtest_mode == "NLP Backtest" else "") / "ProfitInfoLLMs"
                            if backtest_mode == "NLP Backtest":
                                profit_ckpt_dir = BASE_DIR / "ckpt" / "nlp" / "ProfitInfoLLMs"
                            else:
                                profit_ckpt_dir = BASE_DIR / "ckpt" / "ProfitInfoLLMs"
                            
                            profit_ckpt = find_latest_ckpt_file(str(profit_ckpt_dir))
                            if profit_ckpt:
                                profit_data = load_info_dict(profit_ckpt)
                                if profit_data:
                                    # Get the latest date from any model
                                    latest_date = None
                                    for model_data in profit_data.values():
                                        if isinstance(model_data, dict):
                                            dates = [d for d in model_data.keys() if isinstance(d, str)]
                                            if dates:
                                                model_latest = max(dates)
                                                if latest_date is None or model_latest > latest_date:
                                                    latest_date = model_latest
                                    
                                    if latest_date:
                                        st.caption(f"Last processed date: {latest_date}")
                    except Exception as e:
                        st.warning(f"Could not load checkpoint details: {e}")
            else:
                st.warning("⚠️ No checkpoint found. Will start from beginning.")
        
        st.markdown("---")
        
        # Start button
        start_button = st.button("🚀 Start Backtest")
        
        # Stop button (if running)
        if st.session_state.backtest_status == "running":
            stop_button = st.button("⏹️ Stop Backtest")
            if stop_button:
                st.session_state.backtest_status = "stopped"
                st.rerun()
        
        # Data source status
        st.markdown("---")
        st.subheader("📊 Data Source Status")
        data_dir = BASE_DIR / "original_data"
        if data_dir.exists():
            stock_files = list(data_dir.glob("*.csv"))
            st.metric("Stock Count", len(stock_files))
            if stock_files:
                latest_file = max(stock_files, key=lambda f: f.stat().st_mtime)
                st.caption(f"Last Updated: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
        else:
            st.warning("Data directory does not exist")
    
    # Main content area
    # Check if backtest is running
    if st.session_state.backtest_status == "running":
        # Check if thread is still running
        if st.session_state.backtest_thread and not st.session_state.backtest_thread.is_alive():
            # Thread completed, check results (update session_state in main thread)
            result_dict = st.session_state.get("backtest_result_dict", {})
            error_dict = st.session_state.get("backtest_error_dict", {})
            
            # Only consider completed if result_dict explicitly contains "completed" status
            if result_dict.get("status") == "completed" and result_dict.get("result_files"):
                st.session_state.backtest_status = "completed"
                st.session_state.backtest_result = result_dict
                st.rerun()
            elif error_dict.get("error"):
                st.session_state.backtest_status = "failed"
                st.session_state.backtest_error = error_dict.get("error")
                st.rerun()
            else:
                # Thread ended but no results, possibly abnormal exit
                if not result_dict and not error_dict:
                    st.session_state.backtest_status = "failed"
                    st.session_state.backtest_error = "Backtest thread exited abnormally, please check logs"
                    st.rerun()
        
        # Display progress
        st.header("🔄 Backtest Running...")
        
        progress = st.session_state.backtest_progress
        if progress.get("total_days", 0) > 0:
            progress_percent = min(progress["current_day"] / progress["total_days"], 1.0)
            st.progress(progress_percent)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Progress", f"{progress['current_day']}/{progress['total_days']} days")
            with col2:
                if progress.get("start_time"):
                    elapsed = time.time() - progress["start_time"]
                    if progress["current_day"] > 0:
                        avg_time_per_day = elapsed / progress["current_day"]
                        remaining_days = progress["total_days"] - progress["current_day"]
                        estimated_remaining = avg_time_per_day * remaining_days
                        st.metric("Estimated Time Remaining", f"{int(estimated_remaining/60)} min")
                    else:
                        st.metric("Elapsed Time", f"{int(elapsed/60)} min")
            with col3:
                st.metric("Status", progress.get("message", "Running..."))
        else:
            st.info(progress.get("message", "Initializing..."))
        
        # Auto refresh (every 2 seconds)
        time.sleep(2)
        st.rerun()
    
    # Start backtest
    elif start_button and selected_models:
        if start_date >= end_date:
            st.error("❌ Start date must be earlier than end date")
        else:
            # Create configuration
            config = BacktestConfig(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                initial_cash=initial_cash,
                models=selected_models,
                history=history,
                debug=False,
            )
            
            # Reset state
            st.session_state.backtest_status = "running"
            st.session_state.backtest_mode = backtest_mode  # Save backtest mode
            st.session_state.backtest_progress = {
                "current_day": 0,
                "total_days": 0,
                "models_status": {},
                "message": "Initializing...",
                "start_time": None,
            }
            st.session_state.backtest_result = None
            st.session_state.backtest_error = None
            
            # Create result dictionaries (for inter-thread communication)
            progress_dict = st.session_state.backtest_progress
            result_dict = {}  # Background thread writes results here
            error_dict = {}  # Background thread writes errors here
            st.session_state.backtest_result_dict = result_dict  # Save reference for main thread to read
            st.session_state.backtest_error_dict = error_dict
            
            # Start background thread
            if backtest_mode == "Numeric Backtest":
                thread = threading.Thread(
                    target=run_numeric_backtest,
                    args=(config, progress_dict, result_dict, error_dict, resume_from_checkpoint, model_resume_dates),
                    daemon=True,
                )
            else:
                thread = threading.Thread(
                    target=run_nlp_backtest,
                    args=(config, progress_dict, result_dict, error_dict, resume_from_checkpoint, model_resume_dates),
                    daemon=True,
                )
            
            thread.start()
            st.session_state.backtest_thread = thread
            
            st.rerun()
    
    # Display results
    elif st.session_state.backtest_result or st.session_state.backtest_status == "completed":
        st.header("✅ Backtest Completed")
        
        # Load results
        if st.session_state.backtest_result is None:
            # Get result files from progress
            result_files = []
            nlp_files = []
            results_dir = BASE_DIR / "results"
            nlp_dir = BASE_DIR / "results_nlp"
            
            # Get backtest mode from session_state
            saved_mode = st.session_state.get("backtest_mode", "Numeric Backtest")
            
            if results_dir.exists():
                # Get model list from result_dict, or from progress if not available
                result_dict = st.session_state.get("backtest_result_dict", {})
                models = result_dict.get("models", st.session_state.backtest_progress.get("models", []))
                
                for model in models:
                    csv_file = results_dir / f"{model}.csv"
                    if csv_file.exists():
                        result_files.append(str(csv_file))
                    if saved_mode == "NLP Backtest":
                        nlp_file = nlp_dir / f"{model}_nlp.jsonl"
                        if nlp_file.exists():
                            nlp_files.append(str(nlp_file))
            
            st.session_state.backtest_result = {
                "result_files": result_files,
                "nlp_files": nlp_files if saved_mode == "NLP Backtest" else [],
            }
        
        result = st.session_state.backtest_result
        saved_mode = st.session_state.get("backtest_mode", "Numeric Backtest")
        
        # If NLP backtest, show a notification first
        if saved_mode == "NLP Backtest":
            if result.get("nlp_files"):
                st.success("✅ NLP Backtest Mode: Natural language decision logs saved. View AI decision reasons below.")
            else:
                st.warning("⚠️ NLP Backtest Mode: NLP log files not found")
        
        # NLP log viewer (display early for better visibility)
        if saved_mode == "NLP Backtest" and result.get("nlp_files"):
            st.markdown("---")
            st.subheader("💬 AI Decision Logs & Explainability Analysis")
            st.markdown("**View AI decision reasons and reasoning process for each trading day**")
            
            nlp_logs = load_nlp_logs(result["nlp_files"])
            
            if nlp_logs:
                selected_nlp_model = st.selectbox(
                    "Select Model to View Decision Logs",
                    options=list(nlp_logs.keys()),
                    format_func=lambda x: MODEL_OPTIONS.get(x, x),
                    key="nlp_model_selector",
                )
                
                if selected_nlp_model in nlp_logs:
                    logs = nlp_logs[selected_nlp_model]
                    
                    # Date selector
                    dates = sorted(set(log["date"] for log in logs), reverse=True)
                    selected_date = st.selectbox(
                        "Select Trading Day",
                        options=dates,
                        key="nlp_date_selector",
                        help="Select a trading day to view all trading decisions for that day"
                    )
                    
                    # Display logs for that day
                    day_logs = [log for log in logs if log["date"] == selected_date]
                    
                    if day_logs:
                        log = day_logs[0]  # Should only be one log per day
                        
                        # Parsed actions (contains decision reasons for each stock)
                        parsed_actions = log.get("parsed_actions", {})
                        
                        if parsed_actions:
                            st.markdown(f"#### 📈 {selected_date} Trading Decision Details")
                            
                            # Display decisions by stock
                            for stock_symbol, action in parsed_actions.items():
                                if isinstance(action, dict):
                                    with st.expander(f"**{stock_symbol}** - {action.get('signal', 'N/A').upper()}", expanded=False):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("**Trading Signal**")
                                            signal = action.get("signal", "N/A")
                                            if signal == "entry":
                                                st.success(f"🟢 Buy ({signal})")
                                            elif signal == "close":
                                                st.error(f"🔴 Sell ({signal})")
                                            elif signal == "hold":
                                                st.info(f"🟡 Hold ({signal})")
                                            else:
                                                st.write(signal)
                                            
                                            st.markdown("**Price Information**")
                                            if "current_price" in action:
                                                st.metric("Current Price", f"${action['current_price']:.2f}")
                                            if "profit_target" in action and action["profit_target"]:
                                                st.metric("Target Price", f"${action['profit_target']:.2f}", 
                                                         delta=f"+{((action['profit_target'] / action.get('current_price', 1) - 1) * 100):.2f}%")
                                            if "stop_loss" in action and action["stop_loss"]:
                                                st.metric("Stop Loss", f"${action['stop_loss']:.2f}",
                                                         delta=f"{((action['stop_loss'] / action.get('current_price', 1) - 1) * 100):.2f}%")
                                        
                                        with col2:
                                            st.markdown("**Risk Parameters**")
                                            if "leverage" in action and action["leverage"]:
                                                st.metric("Leverage", f"{action['leverage']}x")
                                            if "confidence" in action:
                                                confidence = action["confidence"]
                                                st.metric("Confidence", f"{confidence*100:.1f}%")
                                            if "risk_usd" in action:
                                                st.metric("Risk Amount", f"${action['risk_usd']:.2f}")
                                        
                                        # Decision reason (justification) - most important part
                                        if "justification" in action and action["justification"]:
                                            st.markdown("**🤔 AI Decision Reason**")
                                            st.info(action["justification"])
                                        else:
                                            st.warning("⚠️ This decision has no reason provided")
                            
                            st.markdown("---")
                            
                            # Account status comparison
                            st.markdown("#### 📊 Account Status Changes")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Before Trading**")
                                account_before = log.get("account_before", {})
                                if account_before:
                                    st.metric("Account Value", f"${account_before.get('currentAccountValue', 0):,.2f}")
                                    st.metric("Available Cash", f"${account_before.get('availableCash', 0):,.2f}")
                                    st.metric("Total Return", f"{account_before.get('totalReturnPercent', 0)*100:.2f}%")
                                    positions_before = account_before.get("positions", {})
                                    if positions_before:
                                        st.markdown(f"**Position Count**: {len(positions_before)}")
                            with col2:
                                st.markdown("**After Trading**")
                                account_after = log.get("account_after", {})
                                if account_after:
                                    st.metric("Account Value", f"${account_after.get('currentAccountValue', 0):,.2f}")
                                    st.metric("Available Cash", f"${account_after.get('availableCash', 0):,.2f}")
                                    st.metric("Total Return", f"{account_after.get('totalReturnPercent', 0)*100:.2f}%")
                                    positions_after = account_after.get("positions", {})
                                    if positions_after:
                                        st.markdown(f"**Position Count**: {len(positions_after)}")
                            
                            # Raw output (expandable)
                            with st.expander("🔍 View Raw LLM Output (JSON Format)", expanded=False):
                                st.text_area(
                                    "Raw Decision Content",
                                    value=log.get("raw_output", ""),
                                    height=300,
                                    disabled=True,
                                )
                        else:
                            st.warning("No trading actions for this trading day")
                    else:
                        st.warning(f"No logs found for {selected_date}")
            else:
                st.warning("⚠️ No NLP log files found, please ensure you ran NLP Backtest mode")
            
            st.markdown("---")
        
        if result["result_files"]:
            # Load data
            dfs = load_results(result["result_files"])
            
            if dfs:
                # Plot charts
                st.subheader("📊 Profit Curves")
                fig = plot_profit_curves(dfs)
                st.plotly_chart(fig)
                
                # Display data table
                st.subheader("📋 Detailed Data")
                selected_model = st.selectbox(
                    "Select Model to View Details",
                    options=list(dfs.keys()),
                    format_func=lambda x: MODEL_OPTIONS.get(x, x),
                )
                
                if selected_model in dfs:
                    df = dfs[selected_model]
                    
                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        final_return = df["ReturnPercent"].iloc[-1] * 100
                        st.metric("Total Return", f"{final_return:.2f}%")
                    with col2:
                        max_value = df["AccountValue"].max()
                        st.metric("Max Account Value", f"${max_value:,.2f}")
                    with col3:
                        min_value = df["AccountValue"].min()
                        st.metric("Min Account Value", f"${min_value:,.2f}")
                    with col4:
                        final_value = df["AccountValue"].iloc[-1]
                        st.metric("Final Account Value", f"${final_value:,.2f}")
                    
                    # Data table
                    st.dataframe(df)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{selected_model}_backtest_results.csv",
                        mime="text/csv",
                    )
    
    # Display error
    elif st.session_state.backtest_error:
        st.error(f"❌ Backtest Failed: {st.session_state.backtest_error}")
        st.session_state.backtest_status = None
    
    # Initial state
    else:
        st.info("👈 Please configure backtest parameters on the left, then click 'Start Backtest' button")


if __name__ == "__main__":
    main()

