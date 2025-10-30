#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API Execution Script
Runs the complete sentiment-based trading backtesting system using DeepSeek API
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import SentimentBacktestingPipeline


def run_deepseek_backtest():
    """Run the complete backtesting system using DeepSeek API"""
    print("🚀 Sentiment-Based Trading Backtesting System (DeepSeek API)")
    print("=" * 70)
    print("🌐 Using DeepSeek API for sentiment analysis")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # API key is set directly in sentiment_analyzer_deepseek.py
    
    # Initialize pipeline with DeepSeek
    pipeline = SentimentBacktestingPipeline(
        data_dir="/root/quant/data/dogs_of_30_mdna",
        output_dir="/root/quant/backtesting/results_deepseek",
        start_date="2020-01-01",
        end_date="2024-12-31",
        sentiment_analyzer_type="deepseek"
    )
    
    print("📊 Configuration:")
    print(f"  Period: 2020 Q1 - 2024 Q4")
    print(f"  Initial Capital: $300,000")
    print(f"  Order Value: $10,000 per trade")
    print(f"  Signal Thresholds: Buy ≥ 60, Sell ≤ 40")
    print(f"  Sentiment Analyzer: DeepSeek API")
    print(f"  Output Directory: {pipeline.output_dir}")
    print()
    
    try:
        # Test DeepSeek API connection first
        print("🔍 Testing DeepSeek API connection...")
        from sentiment_analyzer_deepseek import DeepSeekSentimentAnalyzer
        analyzer = DeepSeekSentimentAnalyzer()
        
        if not analyzer.test_api_connection():
            print("❌ DeepSeek API connection failed")
            print("🔧 Please check your API key and network connection")
            return 1
        
        print("✅ DeepSeek API connection successful")
        print()
        
        # Run three-strategy comparison backtesting
        print("🚀 Starting three-strategy comparison backtesting...")
        results = pipeline.run_three_strategy_comparison()
        
        if 'error' in results:
            print(f"❌ Backtesting failed: {results['error']}")
            return 1
        
        print("\n🎉 Backtesting completed successfully!")
        print(f"📁 Results saved to: {results.get('output_dir', '/root/quant/backtesting/results_deepseek')}")
        
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
                print(f"\n📊 Final Results (Original Strategy - DeepSeek):")
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
                print(f"\n📊 Final Results (Top-K Strategy - DeepSeek):")
                print(f"  Portfolio Value: ${final_value:,.2f}")
                print(f"  Total Return: {total_return:+.2f}%")
        
        return 0
        
    except Exception as e:
        print(f"❌ Backtesting failed with error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check if all dependencies are installed: pip install -r requirements.txt")
        print("  2. Verify data directory exists: /root/quant/data/dogs_of_30_mdna/")
        print("  3. Ensure DEEPSEEK_API_KEY is set correctly")
        print("  4. Check your internet connection for API access")
        return 1


if __name__ == "__main__":
    exit_code = run_deepseek_backtest()
    sys.exit(exit_code)
