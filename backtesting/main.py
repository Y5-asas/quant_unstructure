#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Execution Script for Sentiment-Based Trading Backtesting
Integrates all components to run complete backtesting pipeline
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from typing import Dict

# Force all HuggingFace downloads to use mirror
os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sentiment_analyzer import FinancialSentimentAnalyzer
from sentiment_analyzer_deepseek import DeepSeekSentimentAnalyzer
from trading_strategy import SentimentTradingStrategy
from backtesting_engine import BacktestingEngine
from evaluation_metrics import PerformanceMetrics
from plotting_functions import BacktestingPlots


class SentimentBacktestingPipeline:
    """Main pipeline for sentiment-based trading backtesting"""
    
    def __init__(self, 
                 data_dir: str = "/root/quant/data/dogs_of_30_mdna",
                 output_dir: str = "/root/quant/backtesting/results",
                 start_date: str = "2020-01-01",
                 end_date: str = "2024-12-31",
                 sentiment_analyzer_type: str = "fingpt"):
        """
        Initialize the backtesting pipeline
        
        Args:
            data_dir: Directory containing financial reports
            output_dir: Output directory for results
            start_date: Backtesting start date
            end_date: Backtesting end date
            sentiment_analyzer_type: Type of sentiment analyzer ("fingpt" or "deepseek")
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.start_date = start_date
        self.end_date = end_date
        self.sentiment_analyzer_type = sentiment_analyzer_type
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize components
        self.backtesting_engine = BacktestingEngine(
            data_dir=data_dir,
            start_date=start_date,
            end_date=end_date
        )
        self.metrics_calculator = PerformanceMetrics()
        self.plotter = BacktestingPlots()
        
        # Results storage
        self.backtest_results = None
        self.strategy_metrics = None
        self.buy_hold_metrics = None
    
    def run_complete_backtest(self) -> Dict:
        """
        Run the complete backtesting pipeline
        
        Returns:
            Dictionary with all results
        """
        print("🚀 Starting Complete Sentiment-Based Trading Backtesting Pipeline")
        print("=" * 80)
        
        # Step 1: Run backtesting
        print("\n📊 Step 1: Running Backtesting Engine...")
        self.backtest_results = self.backtesting_engine.run_backtest()
        
        if 'error' in self.backtest_results:
            print(f"❌ Backtesting failed: {self.backtest_results['error']}")
            return self.backtest_results
        
        # Step 2: Calculate performance metrics
        print("\n📈 Step 2: Calculating Performance Metrics...")
        self._calculate_metrics()
        
        # Step 3: Generate plots and tables
        print("\n📊 Step 3: Generating Visualizations...")
        self._generate_visualizations()
        
        # Step 4: Save results
        print("\n💾 Step 4: Saving Results...")
        self._save_results()
        
        # Step 5: Print summary
        print("\n📋 Step 5: Final Summary...")
        self._print_summary()
        
        print("\n✅ Complete Backtesting Pipeline Finished!")
        print("=" * 80)
        
        return {
            'backtest_results': self.backtest_results,
            'strategy_metrics': self.strategy_metrics,
            'buy_hold_metrics': self.buy_hold_metrics,
            'output_dir': self.output_dir
        }
    
    def run_three_strategy_comparison(self) -> Dict:
        """
        Run comparison between three strategies: Original Sentiment, Top-K Sentiment, and Buy&Hold
        
        Returns:
            Dict containing all backtesting results
        """
        print("🚀 Starting Three-Strategy Comparison Pipeline")
        print("=" * 80)
        
        # Step 1: Run backtesting for all three strategies
        print("\n📊 Step 1: Running Backtesting Engine for Three Strategies...")
        
        # Load sentiment data once for the current analyzer type
        print(f"  🔄 Loading sentiment data for {self.sentiment_analyzer_type}...")
        # Initialize a temporary engine to load sentiment data
        temp_engine = BacktestingEngine(
            data_dir=self.data_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            sentiment_analyzer_type=self.sentiment_analyzer_type
        )
        if not temp_engine.load_sentiment_data():
            return {'error': f"Failed to load sentiment data for {self.sentiment_analyzer_type}"}
        preloaded_sentiment_data = temp_engine.sentiment_data
        print(f"  ✅ Sentiment data loaded for {len(preloaded_sentiment_data)} companies.")

        # Save sentiment scores to output directory (as requested by user)
        sentiment_output_path = os.path.join(self.output_dir, f"sentiment_scores_{self.sentiment_analyzer_type}.json")
        try:
            import json
            with open(sentiment_output_path, 'w', encoding='utf-8') as f:
                json.dump(preloaded_sentiment_data, f, indent=2, ensure_ascii=False)
            print(f"  ✅ Saved sentiment scores to {sentiment_output_path}")
        except Exception as e:
            print(f"  ⚠️ Failed to save sentiment scores to {sentiment_output_path}: {e}")

        # Original sentiment strategy
        print("  🔄 Running Original Sentiment Strategy...")
        original_engine = BacktestingEngine(
            data_dir=self.data_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            sentiment_analyzer_type=self.sentiment_analyzer_type
        )
        # Pass preloaded sentiment data to avoid reloading
        original_engine.sentiment_data = preloaded_sentiment_data
        original_results = original_engine.run_backtest()
        
        if 'error' in original_results:
            return {'error': original_results['error']}
        
        # Top-K sentiment strategy (reuse sentiment data)
        print("  🔄 Running Top-K Sentiment Strategy (K=5) - Reusing sentiment data...")
        topk_engine = BacktestingEngine(
            data_dir=self.data_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            top_k=5,
            sentiment_analyzer_type=self.sentiment_analyzer_type
        )
        # Reuse the same sentiment data to avoid reloading
        topk_engine.sentiment_data = preloaded_sentiment_data
        topk_results = topk_engine.run_backtest()
        
        if 'error' in topk_results:
            return {'error': topk_results['error']}
        
        # Buy&Hold strategy (same for both)
        buy_hold_results = original_results['buy_and_hold']
        
        # Step 2: Calculate performance metrics
        print("\n📈 Step 2: Calculating Performance Metrics...")
        
        # Convert strategy performance to DataFrame with proper format for metrics calculation
        original_df = pd.DataFrame(original_results['strategy_performance'])
        topk_df = pd.DataFrame(topk_results['strategy_performance'])
        buy_hold_df = buy_hold_results
        
        # Convert strategy performance to the format expected by evaluation_metrics
        original_metrics_df = self._convert_strategy_to_metrics_format(original_df)
        topk_metrics_df = self._convert_strategy_to_metrics_format(topk_df)
        
        # Calculate metrics with error handling
        try:
            original_metrics = self.metrics_calculator.calculate_all_metrics(original_metrics_df)
        except Exception as e:
            print(f"⚠️ Warning: Could not calculate original strategy metrics: {e}")
            original_metrics = {'Total Return': 0, 'Sharpe Ratio': 0, 'Max Drawdown': 0}
        
        try:
            topk_metrics = self.metrics_calculator.calculate_all_metrics(topk_metrics_df)
        except Exception as e:
            print(f"⚠️ Warning: Could not calculate Top-K strategy metrics: {e}")
            topk_metrics = {'Total Return': 0, 'Sharpe Ratio': 0, 'Max Drawdown': 0}
        
        try:
            buy_hold_metrics = self.metrics_calculator.calculate_all_metrics(buy_hold_df)
        except Exception as e:
            print(f"⚠️ Warning: Could not calculate Buy&Hold metrics: {e}")
            buy_hold_metrics = {'Total Return': 0, 'Sharpe Ratio': 0, 'Max Drawdown': 0}
        
        print("✅ Performance metrics calculated successfully")
        
        # Step 3: Generate visualizations
        print("\n📊 Step 3: Generating Visualizations...")
        try:
            self._generate_three_strategy_visualizations(
                original_results, topk_results, buy_hold_results,
                original_metrics, topk_metrics, buy_hold_metrics
            )
        except Exception as e:
            print(f"⚠️ Warning: Could not generate visualizations: {e}")
            print("📊 Continuing with basic visualization generation...")
            self._generate_basic_visualizations(original_results, buy_hold_results)
        
        # Step 4: Save results
        print("\n💾 Step 4: Saving Results...")
        try:
            self._save_three_strategy_results(
                original_results, topk_results, buy_hold_results,
                original_metrics, topk_metrics, buy_hold_metrics
            )
        except Exception as e:
            print(f"⚠️ Warning: Could not save advanced results: {e}")
            print("💾 Saving basic results...")
            self._save_basic_results(original_results, buy_hold_results)
        
        # Step 5: Final summary
        print("\n📋 Step 5: Final Summary...")
        try:
            self._print_three_strategy_summary(
                original_results, topk_results, buy_hold_results,
                original_metrics, topk_metrics, buy_hold_metrics
            )
        except Exception as e:
            print(f"⚠️ Warning: Could not generate advanced summary: {e}")
            print("📋 Generating basic summary...")
            self._print_basic_summary(original_results, buy_hold_results)
        
        print("\n✅ Three-Strategy Comparison Pipeline Finished!")
        print("=" * 80)
        
        return {
            'original_results': original_results,
            'topk_results': topk_results,
            'buy_hold_results': buy_hold_results,
            'original_metrics': original_metrics,
            'topk_metrics': topk_metrics,
            'buy_hold_metrics': buy_hold_metrics,
            'output_dir': self.output_dir
        }
    
    def _convert_strategy_to_metrics_format(self, strategy_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert strategy performance DataFrame to the format expected by evaluation_metrics
        
        Args:
            strategy_df: DataFrame with strategy performance data
            
        Returns:
            DataFrame with timestamp and portfolio_value columns
        """
        # Extract portfolio values and timestamps
        timestamps = []
        portfolio_values = []
        
        for _, row in strategy_df.iterrows():
            timestamps.append(pd.to_datetime(row['period_end']))
            portfolio_values.append(row['portfolio_summary']['total_portfolio_value'])
        
        # Create DataFrame in the format expected by evaluation_metrics
        metrics_df = pd.DataFrame({
            'timestamp': timestamps,
            'portfolio_value': portfolio_values
        })
        
        # Calculate all required columns for evaluation_metrics
        if len(metrics_df) > 0:
            initial_value = metrics_df['portfolio_value'].iloc[0]
            
            # Calculate returns
            metrics_df['returns'] = metrics_df['portfolio_value'].pct_change(fill_method=None)
            metrics_df['log_returns'] = np.log(metrics_df['portfolio_value'] / metrics_df['portfolio_value'].shift(1))
            metrics_df['cumulative_return'] = (metrics_df['portfolio_value'] / initial_value - 1) * 100
            
            # Calculate compound returns (quarterly)
            metrics_df['compound_return'] = metrics_df['returns'].rolling(window=1).apply(
                lambda x: (1 + x).prod() - 1 if len(x) == 1 else np.nan
            )
        
        return metrics_df

    def _generate_basic_visualizations(self, original_results, buy_hold_results):
        """Generate basic visualizations when advanced ones fail"""
        try:
            # Create simple cumulative returns plot
            import matplotlib.pyplot as plt
            
            original_df = pd.DataFrame(original_results['strategy_performance'])
            buy_hold_df = buy_hold_results
            
            plt.figure(figsize=(12, 8))
            
            # Plot original strategy
            plt.plot(range(len(original_df)), original_df['portfolio_value'], 
                    label='Original Strategy', linewidth=2)
            
            # Plot buy and hold
            plt.plot(range(len(buy_hold_df)), buy_hold_df['portfolio_value'], 
                    label='Buy&Hold', linewidth=2)
            
            plt.title('Portfolio Value Comparison', fontsize=16, fontweight='bold')
            plt.xlabel('Quarter', fontsize=12)
            plt.ylabel('Portfolio Value ($)', fontsize=12)
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Save plot
            plt.savefig(f"{self.output_dir}/basic_cumulative_returns.png", 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
            print("✅ Basic visualization generated successfully")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not generate basic visualizations: {e}")

    def _save_basic_results(self, original_results, buy_hold_results):
        """Save basic results when advanced saving fails"""
        try:
            # Save strategy performance
            strategy_df = pd.DataFrame(original_results['strategy_performance'])
            strategy_df.to_csv(f"{self.output_dir}/strategy_performance.csv", index=False)
            
            # Save buy and hold results
            buy_hold_df = buy_hold_results
            buy_hold_df.to_csv(f"{self.output_dir}/buy_and_hold.csv", index=False)
            
            # Create basic summary
            with open(f"{self.output_dir}/backtesting_summary.txt", "w") as f:
                f.write("Backtesting Results Summary\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Strategy Performance:\n")
                f.write(f"Final Portfolio Value: ${strategy_df.iloc[-1]['portfolio_value']:,.2f}\n")
                f.write(f"Total Return: {((strategy_df.iloc[-1]['portfolio_value'] / 300000) - 1) * 100:.2f}%\n\n")
                f.write(f"Buy&Hold Performance:\n")
                f.write(f"Final Portfolio Value: ${buy_hold_df.iloc[-1]['portfolio_value']:,.2f}\n")
                f.write(f"Total Return: {buy_hold_df.iloc[-1]['cumulative_return']:.2f}%\n")
            
            print("✅ Basic results saved successfully")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not save basic results: {e}")

    def _print_basic_summary(self, original_results, buy_hold_results):
        """Print basic summary when advanced summary fails"""
        try:
            strategy_df = pd.DataFrame(original_results['strategy_performance'])
            buy_hold_df = buy_hold_results
            
            print("\n" + "=" * 60)
            print("📊 BACKTESTING RESULTS SUMMARY")
            print("=" * 60)
            
            print(f"\n🎯 Original Sentiment Strategy:")
            final_strategy_value = strategy_df.iloc[-1]['portfolio_value']
            strategy_return = ((final_strategy_value / 300000) - 1) * 100
            print(f"   Final Portfolio Value: ${final_strategy_value:,.2f}")
            print(f"   Total Return: {strategy_return:.2f}%")
            
            print(f"\n📈 Buy&Hold Strategy:")
            final_bh_value = buy_hold_df.iloc[-1]['portfolio_value']
            bh_return = buy_hold_df.iloc[-1]['cumulative_return']
            print(f"   Final Portfolio Value: ${final_bh_value:,.2f}")
            print(f"   Total Return: {bh_return:.2f}%")
            
            print(f"\n🏆 Performance Comparison:")
            if strategy_return > bh_return:
                print(f"   ✅ Original Strategy outperformed Buy&Hold by {strategy_return - bh_return:.2f}%")
            else:
                print(f"   ❌ Buy&Hold outperformed Original Strategy by {bh_return - strategy_return:.2f}%")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"⚠️ Warning: Could not generate basic summary: {e}")

    def _generate_three_strategy_visualizations(self, 
                                               original_results, topk_results, buy_hold_results,
                                               original_metrics, topk_metrics, buy_hold_metrics):
        """Generate visualizations for three strategies"""
        
        # Prepare data for plotting
        original_df = pd.DataFrame(original_results['strategy_performance']).copy()
        topk_df = pd.DataFrame(topk_results['strategy_performance']).copy()
        buy_hold_df = buy_hold_results.copy()
        
        # Add timestamp columns
        original_df['timestamp'] = pd.to_datetime(original_df['period_end'])
        topk_df['timestamp'] = pd.to_datetime(topk_df['period_end'])
        buy_hold_df['timestamp'] = pd.to_datetime(buy_hold_df['period_end'])
        
        # Create plots - generate separate plots for each strategy comparison
        print("  📊 Creating cumulative returns plot (Original vs Buy&Hold)...")
        fig1 = self.plotter.plot_cumulative_returns(
            original_df, buy_hold_df,
            "FIGURE 1 - Cumulative return of Original Sentiment Strategy vs Buy&Hold",
            save_path=f"{self.output_dir}/cumulative_returns_original_vs_buyhold.png"
        )
        plt.close(fig1)
        
        print("  📊 Creating cumulative returns plot (Top-K vs Buy&Hold)...")
        fig2 = self.plotter.plot_cumulative_returns(
            topk_df, buy_hold_df,
            "FIGURE 1 - Cumulative return of Top-K Sentiment Strategy vs Buy&Hold",
            save_path=f"{self.output_dir}/cumulative_returns_topk_vs_buyhold.png"
        )
        plt.close(fig2)
        
        print("  📈 Creating quarterly compound returns plot (Original vs Buy&Hold)...")
        fig3 = self.plotter.plot_quarterly_compound_returns(
            original_df, buy_hold_df,
            "FIGURE 2 - Quarterly compound return of Original Sentiment Strategy vs Buy&Hold",
            save_path=f"{self.output_dir}/quarterly_compound_returns_original_vs_buyhold.png"
        )
        plt.close(fig3)
        
        print("  📈 Creating quarterly compound returns plot (Top-K vs Buy&Hold)...")
        fig4 = self.plotter.plot_quarterly_compound_returns(
            topk_df, buy_hold_df,
            "FIGURE 2 - Quarterly compound return of Top-K Sentiment Strategy vs Buy&Hold",
            save_path=f"{self.output_dir}/quarterly_compound_returns_topk_vs_buyhold.png"
        )
        plt.close(fig4)
        
        print("  📋 Creating metrics comparison table...")
        fig5 = self.plotter.create_three_strategy_metrics_table(
            original_metrics, topk_metrics, buy_hold_metrics,
            save_path=f"{self.output_dir}/metrics_comparison_three_strategies.png"
        )
        plt.close(fig5)
        
        print("✅ Three-strategy visualizations generated successfully")
    
    def _save_three_strategy_results(self, 
                                    original_results, topk_results, buy_hold_results,
                                    original_metrics, topk_metrics, buy_hold_metrics):
        """Save results for three strategies"""
        
        # Save individual strategy results
        pd.DataFrame(original_results['strategy_performance']).to_csv(
            f"{self.output_dir}/original_strategy_performance.csv", index=False
        )
        pd.DataFrame(topk_results['strategy_performance']).to_csv(
            f"{self.output_dir}/topk_strategy_performance.csv", index=False
        )
        buy_hold_results.to_csv(
            f"{self.output_dir}/buy_hold_performance.csv", index=False
        )
        
        # Save metrics comparison
        analyzer_suffix = "_deepseek" if self.sentiment_analyzer_type == "deepseek" else ""
        metrics_df = pd.DataFrame({
            'Metrics': list(original_metrics.keys()),
            'Original Sentiment': [original_metrics[k] for k in original_metrics.keys()],
            'Top-K Sentiment': [topk_metrics[k] for k in topk_metrics.keys()],
            'Buy&Hold': [buy_hold_metrics[k] for k in buy_hold_metrics.keys()]
        })
        metrics_df.to_csv(f"{self.output_dir}/three_strategy_metrics_comparison{analyzer_suffix}.csv", index=False)
        
        print("✅ Three-strategy results saved successfully")
    
    def _print_three_strategy_summary(self, 
                                     original_results, topk_results, buy_hold_results,
                                     original_metrics, topk_metrics, buy_hold_metrics):
        """Print summary for three strategies"""
        
        print("\n📊 THREE-STRATEGY COMPARISON SUMMARY")
        print("-" * 60)
        
        # Original Strategy
        original_final = original_results['final_portfolio']
        original_return = (original_final['total_portfolio_value'] / 300000 - 1) * 100
        
        print(f"\n🔹 Original Sentiment Strategy:")
        print(f"  Final Value: ${original_final['total_portfolio_value']:,.2f}")
        print(f"  Total Return: {original_return:+.2f}%")
        print(f"  Annual Return: {original_metrics.get('Annual Return', 0):.2f}%")
        print(f"  Sharpe Ratio: {original_metrics.get('Sharpe Ratio', 0):.2f}")
        print(f"  Max Drawdown: {original_metrics.get('Max Drawdown (MDD)', 0):.2f}%")
        
        # Top-K Strategy
        topk_final = topk_results['final_portfolio']
        topk_return = (topk_final['total_portfolio_value'] / 300000 - 1) * 100
        
        print(f"\n🔸 Top-K Sentiment Strategy (K=5):")
        print(f"  Final Value: ${topk_final['total_portfolio_value']:,.2f}")
        print(f"  Total Return: {topk_return:+.2f}%")
        print(f"  Annual Return: {topk_metrics.get('Annual Return', 0):.2f}%")
        print(f"  Sharpe Ratio: {topk_metrics.get('Sharpe Ratio', 0):.2f}")
        print(f"  Max Drawdown: {topk_metrics.get('Max Drawdown (MDD)', 0):.2f}%")
        
        # Buy&Hold Strategy
        buy_hold_final = buy_hold_results.iloc[-1]
        buy_hold_return = (buy_hold_final['portfolio_value'] / 300000 - 1) * 100
        
        print(f"\n🔹 Buy&Hold Strategy:")
        print(f"  Final Value: ${buy_hold_final['portfolio_value']:,.2f}")
        print(f"  Total Return: {buy_hold_return:+.2f}%")
        print(f"  Annual Return: {buy_hold_metrics.get('Annual Return', 0):.2f}%")
        print(f"  Sharpe Ratio: {buy_hold_metrics.get('Sharpe Ratio', 0):.2f}")
        print(f"  Max Drawdown: {buy_hold_metrics.get('Max Drawdown (MDD)', 0):.2f}%")
        
        print(f"\n📁 Results saved to: {self.output_dir}")
    
    def _calculate_metrics(self) -> None:
        """Calculate performance metrics for both strategies"""
        
        # Prepare strategy data
        strategy_data = []
        for result in self.backtest_results['strategy_performance']:
            strategy_data.append({
                'timestamp': result['period_end'],
                'portfolio_value': result['portfolio_summary']['total_portfolio_value']
            })
        
        strategy_df = pd.DataFrame(strategy_data)
        
        # Prepare buy-and-hold data
        buy_hold_df = self.backtest_results['buy_and_hold'].copy()
        buy_hold_df = buy_hold_df.rename(columns={'period_end': 'timestamp'})
        
        # Calculate returns for both strategies
        strategy_returns = self.metrics_calculator.calculate_returns(
            strategy_df['portfolio_value'].tolist(),
            strategy_df['timestamp'].tolist()
        )
        
        buy_hold_returns = self.metrics_calculator.calculate_returns(
            buy_hold_df['portfolio_value'].tolist() if 'portfolio_value' in buy_hold_df.columns else buy_hold_df['return'].tolist(),
            buy_hold_df['timestamp'].tolist()
        )
        
        # Calculate all metrics
        self.strategy_metrics = self.metrics_calculator.calculate_all_metrics(strategy_returns)
        self.buy_hold_metrics = self.metrics_calculator.calculate_all_metrics(buy_hold_returns)
        
        print("✅ Performance metrics calculated successfully")
    
    def _generate_visualizations(self) -> None:
        """Generate all visualization plots and tables"""
        
        # Prepare data for plotting
        strategy_data = []
        for result in self.backtest_results['strategy_performance']:
            total_return = (result['portfolio_summary']['total_portfolio_value'] / 300000 - 1) * 100
            strategy_data.append({
                'timestamp': result['period_end'],
                'portfolio_value': result['portfolio_summary']['total_portfolio_value'],
                'cumulative_return': total_return
            })
        
        strategy_df = pd.DataFrame(strategy_data)
        
        # Prepare buy-and-hold data
        buy_hold_df = self.backtest_results['buy_and_hold'].copy()
        if 'cumulative_return' not in buy_hold_df.columns and 'return' in buy_hold_df.columns:
            buy_hold_df['cumulative_return'] = (1 + buy_hold_df['return']).cumprod() - 1
        
        # Debug: Print buy_hold_df columns
        print(f"🔍 Buy-hold data columns: {list(buy_hold_df.columns)}")
        
        # Ensure timestamp column exists for buy-and-hold data
        if 'timestamp' not in buy_hold_df.columns:
            if 'period_end' in buy_hold_df.columns:
                buy_hold_df['timestamp'] = buy_hold_df['period_end']
                print("✅ Created timestamp from period_end")
            elif 'period_start' in buy_hold_df.columns:
                buy_hold_df['timestamp'] = buy_hold_df['period_start']
                print("✅ Created timestamp from period_start")
            else:
                # Create timestamp from index if it's datetime
                if hasattr(buy_hold_df.index, 'to_pydatetime'):
                    buy_hold_df['timestamp'] = buy_hold_df.index
                    print("✅ Created timestamp from index")
                else:
                    print("❌ Warning: No timestamp column found in buy-and-hold data")
                    # Create a dummy timestamp column
                    buy_hold_df['timestamp'] = pd.date_range('2020-01-01', periods=len(buy_hold_df), freq='Q')
                    print("✅ Created dummy timestamp column")
        
        # Ensure portfolio_value column exists for buy-and-hold data (needed for quarterly calculations)
        if 'portfolio_value' not in buy_hold_df.columns:
            # Create portfolio_value from cumulative_return (assuming starting value of 300000)
            initial_value = 300000
            buy_hold_df['portfolio_value'] = initial_value * (1 + buy_hold_df['cumulative_return'])
        
        # Create plots
        print("  📊 Creating cumulative returns plot...")
        fig1 = self.plotter.plot_cumulative_returns(
            strategy_df, buy_hold_df,
            save_path=f"{self.output_dir}/cumulative_returns.png"
        )
        plt.close(fig1)
        
        print("  📈 Creating quarterly compound returns plot...")
        fig2 = self.plotter.plot_quarterly_compound_returns(
            strategy_df, buy_hold_df,
            save_path=f"{self.output_dir}/quarterly_compound_returns.png"
        )
        plt.close(fig2)
        
        print("  📋 Creating metrics comparison table...")
        fig3 = self.plotter.create_metrics_table(
            self.strategy_metrics, self.buy_hold_metrics,
            save_path=f"{self.output_dir}/metrics_comparison.png"
        )
        plt.close(fig3)
        
        print("✅ Visualizations generated successfully")
    
    def _save_results(self) -> None:
        """Save all results to files"""
        
        # Save backtesting results
        self.backtesting_engine.save_results(self.backtest_results, self.output_dir)
        
        # Save metrics to CSV
        metrics_df = pd.DataFrame({
            'Metrics': list(self.strategy_metrics.keys()),
            'Sentiment Strategy': [self.strategy_metrics[metric] for metric in self.strategy_metrics.keys()],
            'Buy&Hold': [self.buy_hold_metrics[metric] for metric in self.strategy_metrics.keys()]
        })
        metrics_df.to_csv(f"{self.output_dir}/performance_metrics.csv", index=False)
        
        # Save detailed results
        with open(f"{self.output_dir}/backtesting_summary.txt", 'w') as f:
            f.write("Sentiment-Based Trading Backtesting Results\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Period: {self.start_date} to {self.end_date}\n")
            f.write(f"Initial Capital: $300,000\n")
            f.write(f"Order Value: $10,000\n")
            f.write(f"Signal Thresholds: Buy >= 60, Sell <= 40\n\n")
            
            final_portfolio = self.backtest_results['final_portfolio']
            total_return = (final_portfolio['total_portfolio_value'] / 300000 - 1) * 100
            
            f.write(f"Final Results:\n")
            f.write(f"  Portfolio Value: ${final_portfolio['total_portfolio_value']:,.2f}\n")
            f.write(f"  Total Return: {total_return:.2f}%\n")
            f.write(f"  Cash: ${final_portfolio['cash']:,.2f}\n")
            f.write(f"  Positions: {final_portfolio['num_positions']}\n")
        
        print("✅ Results saved successfully")
    
    def _print_summary(self) -> None:
        """Print final summary of results"""
        
        print("\n📊 FINAL RESULTS SUMMARY")
        print("-" * 40)
        
        # Portfolio summary
        final_portfolio = self.backtest_results['final_portfolio']
        total_return = (final_portfolio['total_portfolio_value'] / 300000 - 1) * 100
        
        print(f"💰 Portfolio Performance:")
        print(f"  Initial Capital: $300,000")
        print(f"  Final Value: ${final_portfolio['total_portfolio_value']:,.2f}")
        print(f"  Total Return: {total_return:+.2f}%")
        print(f"  Cash: ${final_portfolio['cash']:,.2f}")
        print(f"  Market Value: ${final_portfolio['total_market_value']:,.2f}")
        print(f"  Active Positions: {final_portfolio['num_positions']}")
        
        # Key metrics comparison
        print(f"\n📈 Key Performance Metrics:")
        key_metrics = ['Annual Return', 'Sharpe Ratio', 'Max Drawdown (MDD)', 'Annual Volatility']
        for metric in key_metrics:
            if metric in self.strategy_metrics:
                strategy_val = self.strategy_metrics[metric]
                buy_hold_val = self.buy_hold_metrics[metric]
                better = "✅" if strategy_val > buy_hold_val else "❌"
                
                if 'Return' in metric or 'Volatility' in metric or 'MDD' in metric:
                    print(f"  {metric}:")
                    print(f"    Strategy: {strategy_val:.2f}% {better}")
                    print(f"    Buy&Hold: {buy_hold_val:.2f}%")
                else:
                    print(f"  {metric}:")
                    print(f"    Strategy: {strategy_val:.2f} {better}")
                    print(f"    Buy&Hold: {buy_hold_val:.2f}")
        
        print(f"\n📁 Results saved to: {self.output_dir}")


def main():
    """Main execution function"""
    print("🚀 Sentiment-Based Trading Backtesting System")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = SentimentBacktestingPipeline(
        data_dir="/root/quant/data/dogs_of_30_mdna",
        output_dir="/root/quant/backtesting/results",
        start_date="2020-01-01",
        end_date="2024-12-31"
    )
    
    # Run complete backtesting
    results = pipeline.run_complete_backtest()
    
    if 'error' in results:
        print(f"❌ Pipeline failed: {results['error']}")
        return 1
    
    print("\n🎉 Backtesting completed successfully!")
    print(f"📁 Check results in: {results['output_dir']}")
    
    return 0


if __name__ == "__main__":
    # Import matplotlib here to avoid issues
    import matplotlib.pyplot as plt
    
    exit_code = main()
    sys.exit(exit_code)
