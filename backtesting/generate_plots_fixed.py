#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed plot generation script for three-strategy comparison
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import ast
import re

def load_and_process_data():
    """Load and process the strategy performance data"""
    
    print("📊 Loading data files...")
    
    # Load data
    original_df = pd.read_csv('results/original_strategy_performance.csv')
    topk_df = pd.read_csv('results/topk_strategy_performance.csv')
    buy_hold_df = pd.read_csv('results/buy_hold_performance.csv')
    
    print(f"✅ Loaded {len(original_df)} original strategy records")
    print(f"✅ Loaded {len(topk_df)} topk strategy records")
    print(f"✅ Loaded {len(buy_hold_df)} buy&hold records")
    
    # Process original strategy data
    original_values = []
    original_dates = []
    for _, row in original_df.iterrows():
        try:
            portfolio_summary = row['portfolio_summary']
            # Clean up the string format
            portfolio_summary = portfolio_summary.replace('np.float64(', '').replace(')', '')
            portfolio_dict = ast.literal_eval(portfolio_summary)
            value = float(portfolio_dict['total_portfolio_value'])
            original_values.append(value)
            original_dates.append(pd.to_datetime(row['period_end']))
        except Exception as e:
            print(f"⚠️ Error processing original strategy data: {e}")
            continue
    
    # Process Top-K strategy data
    topk_values = []
    topk_dates = []
    for _, row in topk_df.iterrows():
        try:
            portfolio_summary = row['portfolio_summary']
            # Clean up the string format
            portfolio_summary = portfolio_summary.replace('np.float64(', '').replace(')', '')
            portfolio_dict = ast.literal_eval(portfolio_summary)
            value = float(portfolio_dict['total_portfolio_value'])
            topk_values.append(value)
            topk_dates.append(pd.to_datetime(row['period_end']))
        except Exception as e:
            print(f"⚠️ Error processing topk strategy data: {e}")
            continue
    
    # Process Buy&Hold data
    buy_hold_values = buy_hold_df['portfolio_value'].tolist()
    buy_hold_dates = pd.to_datetime(buy_hold_df['period_end']).tolist()
    
    print(f"✅ Processed {len(original_values)} original strategy values")
    print(f"✅ Processed {len(topk_values)} topk strategy values")
    print(f"✅ Processed {len(buy_hold_values)} buy&hold values")
    
    return (original_dates, original_values, topk_dates, topk_values, 
            buy_hold_dates, buy_hold_values)

def create_cumulative_returns_plot():
    """Create cumulative returns plot"""
    
    print("📊 Creating cumulative returns plot...")
    
    # Load data
    original_dates, original_values, topk_dates, topk_values, buy_hold_dates, buy_hold_values = load_and_process_data()
    
    # Create plot
    plt.figure(figsize=(14, 8))
    
    # Plot cumulative returns
    if len(original_values) > 0:
        plt.plot(original_dates, original_values, label='Original Sentiment Strategy', linewidth=2, color='blue')
    if len(topk_values) > 0:
        plt.plot(topk_dates, topk_values, label='Top-K Sentiment Strategy (K=5)', linewidth=2, color='red')
    if len(buy_hold_values) > 0:
        plt.plot(buy_hold_dates, buy_hold_values, label='Buy&Hold Strategy', linewidth=2, color='green')
    
    plt.title('FIGURE 1 - Cumulative Portfolio Value Comparison', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Portfolio Value ($)', fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Format y-axis
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save plot
    plt.savefig('results/cumulative_returns_three_strategies.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created cumulative returns plot: results/cumulative_returns_three_strategies.png")

def create_quarterly_returns_plot():
    """Create quarterly returns plot"""
    
    print("📊 Creating quarterly returns plot...")
    
    # Load data
    original_dates, original_values, topk_dates, topk_values, buy_hold_dates, buy_hold_values = load_and_process_data()
    
    # Calculate quarterly returns
    def calculate_quarterly_returns(dates, values):
        if len(values) == 0:
            return [], []
            
        quarterly_returns = []
        quarters = []
        initial_value = 300000  # Starting capital
        
        for i, (date, value) in enumerate(zip(dates, values)):
            if i == 0:
                quarterly_return = (value - initial_value) / initial_value * 100
            else:
                quarterly_return = (value - values[i-1]) / values[i-1] * 100
            
            quarterly_returns.append(quarterly_return)
            quarters.append(date.strftime('%Y-Q%q'))
        
        return quarters, quarterly_returns
    
    # Calculate returns for each strategy
    orig_quarters, orig_returns = calculate_quarterly_returns(original_dates, original_values)
    topk_quarters, topk_returns = calculate_quarterly_returns(topk_dates, topk_values)
    bh_quarters, bh_returns = calculate_quarterly_returns(buy_hold_dates, buy_hold_values)
    
    print(f"📊 Calculated {len(orig_returns)} original quarterly returns")
    print(f"📊 Calculated {len(topk_returns)} topk quarterly returns")
    print(f"📊 Calculated {len(bh_returns)} buy&hold quarterly returns")
    
    # Create plot
    plt.figure(figsize=(14, 8))
    
    # Create bar plot
    if len(orig_returns) > 0:
        x = np.arange(len(orig_quarters))
        width = 0.25
        
        # Plot bars for each strategy
        plt.bar(x - width, orig_returns, width, label='Original Sentiment Strategy', color='blue', alpha=0.7)
        
        if len(topk_returns) > 0:
            # Ensure same length
            min_len = min(len(orig_returns), len(topk_returns))
            plt.bar(x[:min_len], topk_returns[:min_len], width, label='Top-K Sentiment Strategy (K=5)', color='red', alpha=0.7)
        
        if len(bh_returns) > 0:
            # Ensure same length
            min_len = min(len(orig_returns), len(bh_returns))
            plt.bar(x[:min_len] + width, bh_returns[:min_len], width, label='Buy&Hold Strategy', color='green', alpha=0.7)
        
        plt.title('FIGURE 2 - Quarterly Returns Comparison', fontsize=16, fontweight='bold')
        plt.xlabel('Quarter', fontsize=12)
        plt.ylabel('Quarterly Return (%)', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Set x-axis labels
        plt.xticks(x, orig_quarters, rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save plot
    plt.savefig('results/quarterly_returns_three_strategies.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created quarterly returns plot: results/quarterly_returns_three_strategies.png")

def create_metrics_comparison():
    """Create metrics comparison table"""
    
    print("📊 Creating metrics comparison table...")
    
    # Load data
    original_dates, original_values, topk_dates, topk_values, buy_hold_dates, buy_hold_values = load_and_process_data()
    
    # Calculate metrics
    def calculate_metrics(values, name):
        if len(values) == 0:
            return {
                'Strategy': name,
                'Final Value': '$0.00',
                'Total Return': '0.00%',
                'Annual Return': '0.00%',
                'Volatility': '0.00%',
                'Sharpe Ratio': '0.00',
                'Max Drawdown': '0.00%'
            }
        
        initial_value = 300000
        final_value = values[-1]
        total_return = (final_value - initial_value) / initial_value * 100
        
        # Calculate annual return (approximate)
        years = len(values) / 4  # Assuming quarterly data
        if years > 0:
            annual_return = (final_value / initial_value) ** (1/years) - 1
            annual_return *= 100
        else:
            annual_return = 0
        
        # Calculate volatility (simplified)
        if len(values) > 1:
            returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
            volatility = np.std(returns) * np.sqrt(4) * 100  # Annualized
        else:
            volatility = 0
        
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # Calculate max drawdown
        peak = initial_value
        max_dd = 0
        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return {
            'Strategy': name,
            'Final Value': f'${final_value:,.2f}',
            'Total Return': f'{total_return:.2f}%',
            'Annual Return': f'{annual_return:.2f}%',
            'Volatility': f'{volatility:.2f}%',
            'Sharpe Ratio': f'{sharpe_ratio:.2f}',
            'Max Drawdown': f'{max_dd:.2f}%'
        }
    
    # Calculate metrics for each strategy
    metrics_data = [
        calculate_metrics(original_values, 'Original Sentiment Strategy'),
        calculate_metrics(topk_values, 'Top-K Sentiment Strategy (K=5)'),
        calculate_metrics(buy_hold_values, 'Buy&Hold Strategy')
    ]
    
    # Create table
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table
    table_data = []
    headers = ['Strategy', 'Final Value', 'Total Return', 'Annual Return', 'Volatility', 'Sharpe Ratio', 'Max Drawdown']
    
    for metrics in metrics_data:
        row = [metrics[header] for header in headers]
        table_data.append(row)
    
    table = ax.table(cellText=table_data, colLabels=headers, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Style the table
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.title('TABLE 1 - Performance Metrics Comparison', fontsize=16, fontweight='bold', pad=20)
    
    # Save plot
    plt.savefig('results/metrics_comparison_three_strategies.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Created metrics comparison table: results/metrics_comparison_three_strategies.png")

def main():
    """Main function"""
    print("🎨 Generating three-strategy comparison plots (FIXED VERSION)...")
    
    try:
        create_cumulative_returns_plot()
        create_quarterly_returns_plot()
        create_metrics_comparison()
        
        print("\n🎉 All plots generated successfully!")
        print("📁 Files created:")
        print("  - results/cumulative_returns_three_strategies.png")
        print("  - results/quarterly_returns_three_strategies.png")
        print("  - results/metrics_comparison_three_strategies.png")
        
    except Exception as e:
        print(f"❌ Error generating plots: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
