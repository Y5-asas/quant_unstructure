#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Execution Script
Runs the complete sentiment-based trading backtesting system
"""

import os
import sys
from datetime import datetime

# Force all HuggingFace downloads to use mirror
os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"


# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import SentimentBacktestingPipeline


def run_full_backtest():
    """Run the complete backtesting system"""
    print("🚀 Sentiment-Based Trading Backtesting System")
    print("=" * 60)
    print("🌐 Using HF Mirror: https://hf-mirror.com")
    print(f"📁 Cache Directory: {os.environ['HF_HOME']}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize pipeline
    pipeline = SentimentBacktestingPipeline(
        data_dir="/root/quant/data/dogs_of_30_mdna",
        output_dir="/root/quant/backtesting/results",
        start_date="2020-01-01",
        end_date="2024-12-31",
        sentiment_analyzer_type="fingpt"  # Change to "deepseek" to use DeepSeek API
    )
    
    print("📊 Configuration:")
    print(f"  Period: 2020 Q1 - 2024 Q4")
    print(f"  Initial Capital: $300,000")
    print(f"  Order Value: $10,000 per trade")
    print(f"  Signal Thresholds: Buy ≥ 60, Sell ≤ 40")
    print(f"  Output Directory: {pipeline.output_dir}")
    print()
    
    try:
        # Run three-strategy comparison backtesting
        print("🚀 Starting three-strategy comparison backtesting...")
        results = pipeline.run_three_strategy_comparison()
        
        if 'error' in results:
            print(f"❌ Backtesting failed: {results['error']}")
            return 1
        
        print("\n🎉 Backtesting completed successfully!")
        print(f"📁 Results saved to: {results.get('output_dir', '/root/quant/backtesting/results')}")
        
        # Show final results summary
        if 'original_results' in results and 'strategy_performance' in results['original_results']:
            original_df = results['original_results']['strategy_performance']
            if len(original_df) > 0:
                # Extract portfolio value from portfolio_summary
                portfolio_summary = original_df[-1]['portfolio_summary']
                if isinstance(portfolio_summary, str):
                    import ast
                    portfolio_summary = ast.literal_eval(portfolio_summary)
                final_value = portfolio_summary['total_portfolio_value']
                total_return = (final_value / 300000 - 1) * 100
                print(f"\n📊 Final Results (Original Strategy):")
                print(f"  Portfolio Value: ${final_value:,.2f}")
                print(f"  Total Return: {total_return:+.2f}%")
        
        if 'topk_results' in results and 'strategy_performance' in results['topk_results']:
            topk_df = results['topk_results']['strategy_performance']
            if len(topk_df) > 0:
                # Extract portfolio value from portfolio_summary
                portfolio_summary = topk_df[-1]['portfolio_summary']
                if isinstance(portfolio_summary, str):
                    import ast
                    portfolio_summary = ast.literal_eval(portfolio_summary)
                final_value = portfolio_summary['total_portfolio_value']
                total_return = (final_value / 300000 - 1) * 100
                print(f"\n📊 Final Results (Top-K Strategy):")
                print(f"  Portfolio Value: ${final_value:,.2f}")
                print(f"  Total Return: {total_return:+.2f}%")
        
        return 0
        
    except Exception as e:
        print(f"❌ Backtesting failed with error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check if all dependencies are installed: pip install -r requirements.txt")
        print("  2. Verify data directory exists: /root/quant/data/dogs_of_30_mdna/")
        print("  3. Ensure sufficient disk space and memory")
        print("  4. Try running test.py first to verify model loading")
        return 1


if __name__ == "__main__":
    exit_code = run_full_backtest()
    sys.exit(exit_code)
