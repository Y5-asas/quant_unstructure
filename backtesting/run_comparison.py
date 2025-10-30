#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparison Script
Runs both FinGPT and DeepSeek sentiment analysis and generates comparison plots
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import SentimentBacktestingPipeline

def check_existing_results(output_dir: str, check_sentiment_cache: bool = False, analyzer_type: str = None) -> bool:
    """
    Check if results already exist
    
    Args:
        output_dir: Directory containing results
        check_sentiment_cache: If True, also check for sentiment analysis cache
        analyzer_type: Type of analyzer (fingpt or deepseek) for cache checking
    """
    required_files = [
        "original_strategy_performance.csv",
        "topk_strategy_performance.csv", 
        "buy_hold_performance.csv"
    ]
    
    # Check main result files
    for file in required_files:
        if not os.path.exists(os.path.join(output_dir, file)):
            return False
    
    # Optionally check sentiment cache
    if check_sentiment_cache and analyzer_type:
        cache_file = f"/root/quant/backtesting/sentiment_cache_{analyzer_type}.json"
        if not os.path.exists(cache_file):
            return False
    
    return True

def run_comparison():
    """Run comparison between FinGPT and DeepSeek sentiment analysis"""
    print("🚀 Sentiment Analysis Comparison: FinGPT vs DeepSeek")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Run FinGPT analysis
    fingpt_output_dir = "/root/quant/backtesting/results_fingpt"
    # Check if results exist (don't require sentiment cache for FinGPT since it might not have one)
    if check_existing_results(fingpt_output_dir):
        print("✅ FinGPT results already exist, skipping FinGPT analysis")
        fingpt_results = {'status': 'cached'}
    else:
        print("📊 Step 1: Running FinGPT Analysis...")
        fingpt_pipeline = SentimentBacktestingPipeline(
            data_dir="/root/quant/data/dogs_of_30_mdna",
            output_dir=fingpt_output_dir,
            start_date="2020-01-01",
            end_date="2024-12-31",
            sentiment_analyzer_type="fingpt"
        )
        
        fingpt_results = fingpt_pipeline.run_three_strategy_comparison()
        
        if 'error' in fingpt_results:
            print(f"❌ FinGPT analysis failed: {fingpt_results['error']}")
            return 1
        
        print("✅ FinGPT analysis completed")
    
    # Step 2: Run DeepSeek analysis
    deepseek_output_dir = "/root/quant/backtesting/results_deepseek"
    # Check if results exist (don't require sentiment cache for DeepSeek since it might not have one)
    if check_existing_results(deepseek_output_dir):
        print("✅ DeepSeek results already exist, skipping DeepSeek analysis")
        deepseek_results = {'status': 'cached'}
    else:
        print("\n📊 Step 2: Running DeepSeek Analysis...")
        deepseek_pipeline = SentimentBacktestingPipeline(
            data_dir="/root/quant/data/dogs_of_30_mdna",
            output_dir=deepseek_output_dir,
            start_date="2020-01-01",
            end_date="2024-12-31",
            sentiment_analyzer_type="deepseek"
        )
        
        deepseek_results = deepseek_pipeline.run_three_strategy_comparison()
        
        if 'error' in deepseek_results:
            print(f"❌ DeepSeek analysis failed: {deepseek_results['error']}")
            return 1
        
        print("✅ DeepSeek analysis completed")
    
    # Step 3: Generate comparison plots
    print("\n📊 Step 3: Generating Comparison Plots...")
    try:
        generate_comparison_plots(fingpt_results, deepseek_results)
        print("✅ Comparison plots generated successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not generate comparison plots: {e}")
    
    # Step 4: Print summary
    print("\n📋 Step 4: Final Summary...")
    print_comparison_summary(fingpt_results, deepseek_results)
    
    print("\n🎉 Comparison analysis completed successfully!")
    print("📁 Results saved to:")
    print("  - FinGPT: /root/quant/backtesting/results_fingpt/")
    print("  - DeepSeek: /root/quant/backtesting/results_deepseek/")
    print("  - Comparison: /root/quant/backtesting/results_comparison/")
    
    return 0


def generate_comparison_plots(fingpt_results, deepseek_results):
    """Generate comparison plots between FinGPT and DeepSeek results"""
    
    # Create comparison output directory
    comparison_dir = "/root/quant/backtesting/results_comparison"
    os.makedirs(comparison_dir, exist_ok=True)
    
    # Load data directly from saved CSV files (more reliable)
    fingpt_original = pd.read_csv("/root/quant/backtesting/results_fingpt/original_strategy_performance.csv")
    fingpt_topk = pd.read_csv("/root/quant/backtesting/results_fingpt/topk_strategy_performance.csv")
    deepseek_original = pd.read_csv("/root/quant/backtesting/results_deepseek/original_strategy_performance.csv")
    deepseek_topk = pd.read_csv("/root/quant/backtesting/results_deepseek/topk_strategy_performance.csv")
    buy_hold = pd.read_csv("/root/quant/backtesting/results_fingpt/buy_hold_performance.csv")
    
    # Process portfolio values safely
    def extract_portfolio_value(portfolio_summary_str):
        """Safely extract portfolio value from portfolio_summary string"""
        try:
            import ast
            if isinstance(portfolio_summary_str, str):
                portfolio = ast.literal_eval(portfolio_summary_str)
                value = portfolio.get('total_portfolio_value', 0)
                # Handle np.float64 objects
                if hasattr(value, 'item'):
                    return value.item()
                return float(value)
            else:
                value = portfolio_summary_str.get('total_portfolio_value', 0)
                if hasattr(value, 'item'):
                    return value.item()
                return float(value)
        except:
            # Fallback: try to extract number from string
            import re
            # Try np.float64 pattern first
            match = re.search(r"'total_portfolio_value':\s*np\.float64\(([0-9.]+)\)", str(portfolio_summary_str))
            if match:
                return float(match.group(1))
            # Try simpler pattern
            match = re.search(r"'total_portfolio_value':\s*([0-9.]+)", str(portfolio_summary_str))
            if match:
                return float(match.group(1))
            return 0
    
    fingpt_orig_values = fingpt_original['portfolio_summary'].apply(extract_portfolio_value).tolist()
    fingpt_topk_values = fingpt_topk['portfolio_summary'].apply(extract_portfolio_value).tolist()
    deepseek_orig_values = deepseek_original['portfolio_summary'].apply(extract_portfolio_value).tolist()
    deepseek_topk_values = deepseek_topk['portfolio_summary'].apply(extract_portfolio_value).tolist()
    buy_hold_values = buy_hold['portfolio_value'].tolist()
    dates = pd.to_datetime(fingpt_original['period_end']).tolist()
    
    # Plot 1: Cumulative Returns Comparison
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 2, 1)
    plt.plot(dates, fingpt_orig_values, label='FinGPT Original Strategy', linewidth=2, color='blue')
    plt.plot(dates, deepseek_orig_values, label='DeepSeek Original Strategy', linewidth=2, color='red')
    plt.plot(dates, buy_hold_values, label='Buy&Hold', linewidth=2, color='green', linestyle='--')
    plt.title('Original Strategy Comparison: FinGPT vs DeepSeek', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 2)
    plt.plot(dates, fingpt_topk_values, label='FinGPT Top-K Strategy', linewidth=2, color='blue')
    plt.plot(dates, deepseek_topk_values, label='DeepSeek Top-K Strategy', linewidth=2, color='red')
    plt.plot(dates, buy_hold_values, label='Buy&Hold', linewidth=2, color='green', linestyle='--')
    plt.title('Top-K Strategy Comparison: FinGPT vs DeepSeek', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Performance Metrics Comparison
    plt.subplot(2, 2, 3)
    metrics_data = {
        'Strategy': ['FinGPT Original', 'DeepSeek Original', 'FinGPT Top-K', 'DeepSeek Top-K', 'Buy&Hold'],
        'Final Value': [
            fingpt_orig_values[-1],
            deepseek_orig_values[-1],
            fingpt_topk_values[-1],
            deepseek_topk_values[-1],
            buy_hold_values[-1]
        ],
        'Total Return (%)': [
            (fingpt_orig_values[-1] / 300000 - 1) * 100,
            (deepseek_orig_values[-1] / 300000 - 1) * 100,
            (fingpt_topk_values[-1] / 300000 - 1) * 100,
            (deepseek_topk_values[-1] / 300000 - 1) * 100,
            (buy_hold_values[-1] / 300000 - 1) * 100
        ]
    }
    
    df_metrics = pd.DataFrame(metrics_data)
    bars = plt.bar(df_metrics['Strategy'], df_metrics['Total Return (%)'], 
                   color=['blue', 'red', 'lightblue', 'lightcoral', 'green'])
    plt.title('Total Return Comparison', fontsize=14, fontweight='bold')
    plt.ylabel('Total Return (%)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, df_metrics['Total Return (%)']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{value:.1f}%', ha='center', va='bottom')
    
    # Plot 3: Quarterly Returns Comparison
    plt.subplot(2, 2, 4)
    
    # Calculate quarterly returns
    fingpt_orig_returns = []
    deepseek_orig_returns = []
    buy_hold_returns = []
    
    for i in range(1, len(fingpt_orig_values)):
        fingpt_ret = (fingpt_orig_values[i] / fingpt_orig_values[i-1] - 1) * 100
        deepseek_ret = (deepseek_orig_values[i] / deepseek_orig_values[i-1] - 1) * 100
        buy_hold_ret = (buy_hold_values[i] / buy_hold_values[i-1] - 1) * 100
        
        fingpt_orig_returns.append(fingpt_ret)
        deepseek_orig_returns.append(deepseek_ret)
        buy_hold_returns.append(buy_hold_ret)
    
    quarters = [f"Q{i+1}" for i in range(len(fingpt_orig_returns))]
    x = range(len(quarters))
    width = 0.25
    
    plt.bar([i - width for i in x], fingpt_orig_returns, width, label='FinGPT Original', color='blue', alpha=0.7)
    plt.bar(x, deepseek_orig_returns, width, label='DeepSeek Original', color='red', alpha=0.7)
    plt.bar([i + width for i in x], buy_hold_returns, width, label='Buy&Hold', color='green', alpha=0.7)
    
    plt.title('Quarterly Returns Comparison', fontsize=14, fontweight='bold')
    plt.xlabel('Quarter')
    plt.ylabel('Quarterly Return (%)')
    plt.xticks(x, quarters)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{comparison_dir}/finGPT_vs_deepseek_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save comparison data
    comparison_data = {
        'Date': dates,
        'FinGPT_Original': fingpt_orig_values,
        'DeepSeek_Original': deepseek_orig_values,
        'FinGPT_TopK': fingpt_topk_values,
        'DeepSeek_TopK': deepseek_topk_values,
        'Buy_Hold': buy_hold_values
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_csv(f"{comparison_dir}/comparison_data.csv", index=False)
    
    # Save metrics comparison
    df_metrics.to_csv(f"{comparison_dir}/metrics_comparison.csv", index=False)


def print_comparison_summary(fingpt_results, deepseek_results):
    """Print comparison summary"""
    
    print("\n📊 COMPARISON SUMMARY")
    print("-" * 50)
    
    # Check if results are cached
    if fingpt_results.get('status') == 'cached':
        print("✅ FinGPT results loaded from cache")
        # Load final values from CSV files
        fingpt_orig_df = pd.read_csv("/root/quant/backtesting/results_fingpt/original_strategy_performance.csv")
        fingpt_topk_df = pd.read_csv("/root/quant/backtesting/results_fingpt/topk_strategy_performance.csv")
        
        # Extract final portfolio values
        fingpt_orig_final = fingpt_orig_df['portfolio_summary'].iloc[-1]
        fingpt_topk_final = fingpt_topk_df['portfolio_summary'].iloc[-1]
        
        # Parse portfolio values safely
        def safe_extract_portfolio_value(portfolio_str):
            try:
                import ast
                if isinstance(portfolio_str, str):
                    portfolio = ast.literal_eval(portfolio_str)
                    value = portfolio.get('total_portfolio_value', 0)
                    # Handle np.float64 objects
                    if hasattr(value, 'item'):
                        return value.item()
                    return float(value)
                else:
                    value = portfolio_str.get('total_portfolio_value', 0)
                    if hasattr(value, 'item'):
                        return value.item()
                    return float(value)
            except:
                # Fallback: try to extract number from string
                import re
                match = re.search(r"'total_portfolio_value':\s*np\.float64\(([0-9.]+)\)", str(portfolio_str))
                if match:
                    return float(match.group(1))
                # Try simpler pattern
                match = re.search(r"'total_portfolio_value':\s*([0-9.]+)", str(portfolio_str))
                if match:
                    return float(match.group(1))
                return 0
        
        fingpt_orig_value = safe_extract_portfolio_value(fingpt_orig_final)
        fingpt_topk_value = safe_extract_portfolio_value(fingpt_topk_final)
        
        fingpt_orig_return = (fingpt_orig_value / 300000 - 1) * 100
        fingpt_topk_return = (fingpt_topk_value / 300000 - 1) * 100
    else:
        # Use results from memory
        fingpt_orig = fingpt_results['original_results']['final_portfolio']
        fingpt_topk = fingpt_results['topk_results']['final_portfolio']
        fingpt_orig_return = (fingpt_orig['total_portfolio_value'] / 300000 - 1) * 100
        fingpt_topk_return = (fingpt_topk['total_portfolio_value'] / 300000 - 1) * 100
    
    if deepseek_results.get('status') == 'cached':
        print("✅ DeepSeek results loaded from cache")
        # Load final values from CSV files
        deepseek_orig_df = pd.read_csv("/root/quant/backtesting/results_deepseek/original_strategy_performance.csv")
        deepseek_topk_df = pd.read_csv("/root/quant/backtesting/results_deepseek/topk_strategy_performance.csv")
        
        # Extract final portfolio values
        deepseek_orig_final = deepseek_orig_df['portfolio_summary'].iloc[-1]
        deepseek_topk_final = deepseek_topk_df['portfolio_summary'].iloc[-1]
        
        # Parse portfolio values safely
        deepseek_orig_value = safe_extract_portfolio_value(deepseek_orig_final)
        deepseek_topk_value = safe_extract_portfolio_value(deepseek_topk_final)
        
        deepseek_orig_return = (deepseek_orig_value / 300000 - 1) * 100
        deepseek_topk_return = (deepseek_topk_value / 300000 - 1) * 100
    else:
        # Use results from memory
        deepseek_orig = deepseek_results['original_results']['final_portfolio']
        deepseek_topk = deepseek_results['topk_results']['final_portfolio']
        deepseek_orig_return = (deepseek_orig['total_portfolio_value'] / 300000 - 1) * 100
        deepseek_topk_return = (deepseek_topk['total_portfolio_value'] / 300000 - 1) * 100
    
    # Buy&Hold results (same for both)
    buy_hold_df = pd.read_csv("/root/quant/backtesting/results_fingpt/buy_hold_performance.csv")
    buy_hold_final = buy_hold_df.iloc[-1]['portfolio_value']
    buy_hold_return = (buy_hold_final / 300000 - 1) * 100
    
    print(f"\n🔹 FinGPT Results:")
    if fingpt_results.get('status') == 'cached':
        print(f"  Original Strategy: ${fingpt_orig_value:,.2f} ({fingpt_orig_return:+.2f}%)")
        print(f"  Top-K Strategy: ${fingpt_topk_value:,.2f} ({fingpt_topk_return:+.2f}%)")
    else:
        print(f"  Original Strategy: ${fingpt_orig['total_portfolio_value']:,.2f} ({fingpt_orig_return:+.2f}%)")
        print(f"  Top-K Strategy: ${fingpt_topk['total_portfolio_value']:,.2f} ({fingpt_topk_return:+.2f}%)")
    
    print(f"\n🔹 DeepSeek Results:")
    if deepseek_results.get('status') == 'cached':
        print(f"  Original Strategy: ${deepseek_orig_value:,.2f} ({deepseek_orig_return:+.2f}%)")
        print(f"  Top-K Strategy: ${deepseek_topk_value:,.2f} ({deepseek_topk_return:+.2f}%)")
    else:
        print(f"  Original Strategy: ${deepseek_orig['total_portfolio_value']:,.2f} ({deepseek_orig_return:+.2f}%)")
        print(f"  Top-K Strategy: ${deepseek_topk['total_portfolio_value']:,.2f} ({deepseek_topk_return:+.2f}%)")
    
    print(f"\n🔹 Buy&Hold Results:")
    print(f"  Portfolio Value: ${buy_hold_final:,.2f} ({buy_hold_return:+.2f}%)")
    
    print(f"\n📈 Best Performing Strategy:")
    strategies = [
        ("FinGPT Original", fingpt_orig_return),
        ("DeepSeek Original", deepseek_orig_return),
        ("FinGPT Top-K", fingpt_topk_return),
        ("DeepSeek Top-K", deepseek_topk_return),
        ("Buy&Hold", buy_hold_return)
    ]
    
    best_strategy = max(strategies, key=lambda x: x[1])
    print(f"  {best_strategy[0]}: {best_strategy[1]:+.2f}%")


if __name__ == "__main__":
    exit_code = run_comparison()
    sys.exit(exit_code)
