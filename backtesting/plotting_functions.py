#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotting Functions Module
Creates visualization plots for backtesting results similar to the reference images
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import seaborn as sns

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class BacktestingPlots:
    """Create visualization plots for backtesting results"""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """
        Initialize plotting class
        
        Args:
            figsize: Default figure size
        """
        self.figsize = figsize
        self.colors = {
            'Buy&Hold': '#1f77b4',  # Blue
            'Sentiment Strategy': '#ff7f0e',  # Orange
            'Strategy': '#2ca02c',  # Green
            'Model': '#d62728'  # Red
        }
    
    def plot_cumulative_returns(self, 
                               strategy_data: pd.DataFrame,
                               buy_hold_data: pd.DataFrame,
                               title: str = "FIGURE 1 - Cumulative return of all approaches over the backtesting period",
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot cumulative returns similar to Figure 1 from the reference
        
        Args:
            strategy_data: Strategy performance DataFrame
            buy_hold_data: Buy-and-hold performance DataFrame
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Prepare data
        strategy_dates = pd.to_datetime(strategy_data['timestamp'])
        strategy_returns = strategy_data['cumulative_return']
        
        buy_hold_dates = pd.to_datetime(buy_hold_data['timestamp'])
        buy_hold_returns = buy_hold_data['cumulative_return']
        
        # Plot lines
        ax.plot(buy_hold_dates, buy_hold_returns, 
                color=self.colors['Buy&Hold'], linewidth=2, label='Buy&Hold')
        ax.plot(strategy_dates, strategy_returns, 
                color=self.colors['Sentiment Strategy'], linewidth=2, label='Sentiment Strategy')
        
        # Formatting
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative return (%)', fontsize=12)
        
        # Format x-axis dates
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend(loc='upper left', fontsize=11)
        
        # Set y-axis range similar to reference (around -40% to 60%)
        ax.set_ylim(-40, 60)
        
        # Add horizontal line at 0%
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.8)
        
        # Tight layout
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"💾 Plot saved to {save_path}")
        
        return fig
    
    def plot_quarterly_compound_returns(self,
                                       strategy_data: pd.DataFrame,
                                       buy_hold_data: pd.DataFrame,
                                       title: str = "FIGURE 2 – Quarterly compound return of all approaches over the backtesting period",
                                       save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot quarterly compound returns similar to Figure 2 from the reference
        
        Args:
            strategy_data: Strategy performance DataFrame
            buy_hold_data: Buy-and-hold performance DataFrame
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Prepare data - calculate quarterly compound returns
        strategy_quarterly = self._calculate_quarterly_returns(strategy_data)
        buy_hold_quarterly = self._calculate_quarterly_returns(buy_hold_data)
        
        # Plot lines
        ax.plot(buy_hold_quarterly['timestamp'], buy_hold_quarterly['quarterly_return'] * 100, 
                color=self.colors['Buy&Hold'], linewidth=2, label='Buy&Hold')
        ax.plot(strategy_quarterly['timestamp'], strategy_quarterly['quarterly_return'] * 100, 
                color=self.colors['Sentiment Strategy'], linewidth=2, label='Sentiment Strategy')
        
        # Formatting
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Quarterly compound return (%)', fontsize=12)
        
        # Format x-axis dates
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend(loc='upper left', fontsize=11)
        
        # Set y-axis range dynamically based on data
        all_returns = []
        if len(strategy_quarterly) > 0:
            all_returns.extend(strategy_quarterly['quarterly_return'] * 100)
        if len(buy_hold_quarterly) > 0:
            all_returns.extend(buy_hold_quarterly['quarterly_return'] * 100)
        
        if all_returns:
            min_return = min(all_returns)
            max_return = max(all_returns)
            # Add some padding
            padding = (max_return - min_return) * 0.1
            ax.set_ylim(min_return - padding, max_return + padding)
        else:
            # Fallback range
            ax.set_ylim(-20, 20)
        
        # Add horizontal line at 0%
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.8)
        
        # Tight layout
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"💾 Plot saved to {save_path}")
        
        return fig
    
    def _calculate_quarterly_returns(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate quarterly returns from data
        
        Args:
            data: DataFrame with timestamp and portfolio_value columns
            
        Returns:
            DataFrame with quarterly returns
        """
        # Debug: Print data info
        print(f"🔍 Input data columns: {list(data.columns)}")
        print(f"🔍 Input data shape: {data.shape}")
        
        # Ensure data is sorted by timestamp
        data_sorted = data.sort_values('timestamp').copy()
        
        # Convert timestamp to datetime if it's not already
        data_sorted['timestamp'] = pd.to_datetime(data_sorted['timestamp'])
        
        # Group by quarters
        data_sorted['quarter'] = data_sorted['timestamp'].dt.to_period('Q')
        
        quarterly_data = []
        for quarter, group in data_sorted.groupby('quarter'):
            print(f"🔍 Processing quarter: {quarter}, group size: {len(group)}")
            
            # For quarterly data, we might have only one data point per quarter
            # In that case, we can use the cumulative return directly
            if len(group) == 1:
                # Single data point per quarter - use cumulative return if available
                if 'cumulative_return' in group.columns:
                    quarterly_return = group['cumulative_return'].iloc[0]
                else:
                    # Calculate from portfolio value change
                    portfolio_value = group['portfolio_value'].iloc[0]
                    if not pd.isna(portfolio_value) and portfolio_value > 0:
                        quarterly_return = (portfolio_value - 300000) / 300000  # Assuming 300k initial
                    else:
                        quarterly_return = 0.0
            else:
                # Multiple data points - calculate from start to end
                start_value = group['portfolio_value'].iloc[0]
                end_value = group['portfolio_value'].iloc[-1]
                
                # Handle NaN values
                if pd.isna(start_value) or pd.isna(end_value) or start_value == 0:
                    quarterly_return = 0.0
                else:
                    quarterly_return = (end_value - start_value) / start_value
            
            # Convert quarter period to datetime
            quarter_end_time = quarter.end_time
            
            quarterly_data.append({
                'timestamp': quarter_end_time,
                'quarterly_return': quarterly_return
            })
        
        result_df = pd.DataFrame(quarterly_data)
        print(f"🔍 Quarterly returns data shape: {result_df.shape}")
        print(f"🔍 Quarterly returns columns: {list(result_df.columns)}")
        if len(result_df) > 0:
            print(f"🔍 Sample quarterly returns: {result_df.head()}")
        
        return result_df
    
    def create_metrics_table(self, 
                           strategy_metrics: Dict[str, float],
                           buy_hold_metrics: Dict[str, float],
                           title: str = "TABLE 1 – Backtesting results over the period between January 1st, 2020, and December 31st, 2024",
                           save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a metrics comparison table similar to Table 1 from the reference
        
        Args:
            strategy_metrics: Strategy performance metrics
            buy_hold_metrics: Buy-and-hold performance metrics
            title: Table title
            save_path: Optional path to save the table
            
        Returns:
            Matplotlib figure
        """
        # Create comparison DataFrame
        comparison_data = []
        for metric in strategy_metrics.keys():
            strategy_val = strategy_metrics[metric]
            buy_hold_val = buy_hold_metrics[metric]
            
            # Determine which is better
            is_better_strategy = self._is_better_metric(metric, strategy_val, buy_hold_val)
            
            comparison_data.append({
                'Metrics': metric,
                'Buy&Hold': f"{buy_hold_val:.2f}{'%' if 'Return' in metric or 'Volatility' in metric or 'VaR' in metric or 'MDD' in metric else ''}",
                'Sentiment Strategy': f"{strategy_val:.2f}{'%' if 'Return' in metric or 'Volatility' in metric or 'VaR' in metric or 'MDD' in metric else ''}",
                'Strategy Better': is_better_strategy
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Create figure and table
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table_data = []
        for _, row in df.iterrows():
            if row['Strategy Better']:
                strategy_val = f"**{row['Sentiment Strategy']}**"
            else:
                strategy_val = row['Sentiment Strategy']
            
            table_data.append([
                row['Metrics'],
                row['Buy&Hold'],
                strategy_val
            ])
        
        table = ax.table(cellText=table_data,
                        colLabels=['Metrics', 'Buy&Hold', 'Sentiment Strategy'],
                        cellLoc='center',
                        loc='center',
                        bbox=[0, 0, 1, 1])
        
        # Format table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # Style the table
        for i in range(len(table_data) + 1):
            for j in range(3):
                cell = table[(i, j)]
                if i == 0:  # Header row
                    cell.set_facecolor('#40466e')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#f1f1f2' if i % 2 == 0 else 'white')
        
        # Add title
        plt.title(title, fontsize=12, fontweight='bold', pad=20)
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"💾 Table saved to {save_path}")
        
        return fig
    
    def _is_better_metric(self, metric: str, strategy_val: float, buy_hold_val: float) -> bool:
        """
        Determine if strategy value is better than buy-and-hold for a given metric
        
        Args:
            metric: Metric name
            strategy_val: Strategy metric value
            buy_hold_val: Buy-and-hold metric value
            
        Returns:
            True if strategy is better, False otherwise
        """
        # For risk metrics, lower is better
        risk_metrics = ['Max Drawdown (MDD)', 'Annual Volatility', '95% Daily VaR']
        
        if any(risk in metric for risk in risk_metrics):
            return strategy_val < buy_hold_val
        
        # For return and ratio metrics, higher is better
        return strategy_val > buy_hold_val
    
    def plot_portfolio_evolution(self, 
                               portfolio_history: List[Dict],
                               title: str = "Portfolio Evolution Over Time",
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot portfolio evolution showing cash, positions, and total value
        
        Args:
            portfolio_history: List of portfolio states over time
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure
        """
        if not portfolio_history:
            raise ValueError("No portfolio history data provided")
        
        # Extract data
        timestamps = [pd.to_datetime(state['timestamp']) for state in portfolio_history]
        cash_values = [state['cash'] for state in portfolio_history]
        market_values = [state['total_market_value'] for state in portfolio_history]
        total_values = [state['total_portfolio_value'] for state in portfolio_history]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot portfolio values
        ax1.plot(timestamps, total_values, label='Total Portfolio Value', linewidth=2, color='green')
        ax1.plot(timestamps, cash_values, label='Cash', linewidth=2, color='blue')
        ax1.plot(timestamps, market_values, label='Market Value', linewidth=2, color='orange')
        
        ax1.set_title('Portfolio Value Evolution', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Value ($)', fontsize=12)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Plot number of positions
        num_positions = [state['num_positions'] for state in portfolio_history]
        ax2.plot(timestamps, num_positions, marker='o', linewidth=2, color='red')
        
        ax2.set_title('Number of Positions Over Time', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Number of Positions', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"💾 Plot saved to {save_path}")
        
        return fig
    
    def create_three_strategy_metrics_table(self, 
                                           strategy_metrics: Dict[str, float],
                                           topk_metrics: Dict[str, float],
                                           buy_hold_metrics: Dict[str, float],
                                           title: str = "TABLE 1 – Backtesting results over the period between January 1st, 2020, and December 31st, 2024",
                                           save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a metrics comparison table for three strategies
        
        Args:
            strategy_metrics: Original strategy performance metrics
            topk_metrics: Top-K strategy performance metrics
            buy_hold_metrics: Buy-and-hold performance metrics
            title: Table title
            save_path: Optional path to save the table
            
        Returns:
            Matplotlib figure
        """
        # Create comparison DataFrame
        comparison_data = []
        for metric in strategy_metrics.keys():
            strategy_val = strategy_metrics[metric]
            topk_val = topk_metrics[metric]
            buy_hold_val = buy_hold_metrics[metric]
            
            # Determine which is better
            is_better_strategy = self._is_better_metric(metric, strategy_val, buy_hold_val)
            is_better_topk = self._is_better_metric(metric, topk_val, buy_hold_val)
            
            comparison_data.append({
                'Metrics': metric,
                'Buy&Hold': f"{buy_hold_val:.2f}{'%' if 'Return' in metric or 'Volatility' in metric or 'VaR' in metric or 'MDD' in metric else ''}",
                'Original Strategy': f"{strategy_val:.2f}{'%' if 'Return' in metric or 'Volatility' in metric or 'VaR' in metric or 'MDD' in metric else ''}",
                'Top-K Strategy': f"{topk_val:.2f}{'%' if 'Return' in metric or 'Volatility' in metric or 'VaR' in metric or 'MDD' in metric else ''}",
                'Strategy Better': is_better_strategy,
                'Top-K Better': is_better_topk
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Create figure and table
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table_data = []
        for _, row in df.iterrows():
            if row['Strategy Better']:
                strategy_val = f"**{row['Original Strategy']}**"
            else:
                strategy_val = row['Original Strategy']
            
            if row['Top-K Better']:
                topk_val = f"**{row['Top-K Strategy']}**"
            else:
                topk_val = row['Top-K Strategy']
            
            table_data.append([
                row['Metrics'],
                row['Buy&Hold'],
                strategy_val,
                topk_val
            ])
        
        table = ax.table(cellText=table_data,
                        colLabels=['Metrics', 'Buy&Hold', 'Original Strategy', 'Top-K Strategy'],
                        cellLoc='center',
                        loc='center',
                        bbox=[0, 0, 1, 1])
        
        # Format table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # Style header row
        for i in range(4):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Add title
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.95)
        
        # Tight layout
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"💾 Table saved to {save_path}")
        
        return fig
    
    def create_summary_report(self, 
                            strategy_metrics: Dict[str, float],
                            buy_hold_metrics: Dict[str, float],
                            output_dir: str = "/root/quant/backtesting/results") -> None:
        """
        Create a comprehensive summary report with all plots and tables
        
        Args:
            strategy_metrics: Strategy performance metrics
            buy_hold_metrics: Buy-and-hold performance metrics
            output_dir: Output directory for saving files
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print("📊 Creating summary report...")
        
        # Create metrics table
        table_fig = self.create_metrics_table(
            strategy_metrics, buy_hold_metrics,
            save_path=f"{output_dir}/metrics_table.png"
        )
        plt.close(table_fig)
        
        print("✅ Summary report created!")
        print(f"📁 Files saved to: {output_dir}")


def test_plotting_functions():
    """Test the plotting functions with sample data"""
    print("🚀 Testing Plotting Functions...")
    
    # Create sample data
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Generate sample strategy data
    strategy_returns = np.random.normal(0.0015, 0.015, 100)  # Slightly better than buy-and-hold
    strategy_values = [100000]
    for ret in strategy_returns[1:]:
        strategy_values.append(strategy_values[-1] * (1 + ret))
    
    strategy_data = pd.DataFrame({
        'timestamp': dates,
        'portfolio_value': strategy_values,
        'cumulative_return': [(v / strategy_values[0] - 1) * 100 for v in strategy_values]
    })
    
    # Generate sample buy-and-hold data
    bh_returns = np.random.normal(0.001, 0.02, 100)
    bh_values = [100000]
    for ret in bh_returns[1:]:
        bh_values.append(bh_values[-1] * (1 + ret))
    
    buy_hold_data = pd.DataFrame({
        'timestamp': dates,
        'portfolio_value': bh_values,
        'cumulative_return': [(v / bh_values[0] - 1) * 100 for v in bh_values]
    })
    
    # Initialize plotting class
    plotter = BacktestingPlots()
    
    # Test cumulative returns plot
    fig1 = plotter.plot_cumulative_returns(strategy_data, buy_hold_data)
    plt.show()
    plt.close(fig1)
    
    # Test quarterly compound returns plot
    fig2 = plotter.plot_quarterly_compound_returns(strategy_data, buy_hold_data)
    plt.show()
    plt.close(fig2)
    
    # Test metrics table
    sample_strategy_metrics = {
        'Annual Return': 12.5,
        'Annual Compound Return': 15.2,
        'Sharpe Ratio': 1.8,
        'Max Drawdown (MDD)': -8.5,
        'Annual Volatility': 12.3
    }
    
    sample_bh_metrics = {
        'Annual Return': 10.2,
        'Annual Compound Return': 12.8,
        'Sharpe Ratio': 1.2,
        'Max Drawdown (MDD)': -15.6,
        'Annual Volatility': 18.4
    }
    
    fig3 = plotter.create_metrics_table(sample_strategy_metrics, sample_bh_metrics)
    plt.show()
    plt.close(fig3)
    
    print("✅ Plotting functions test completed!")


if __name__ == "__main__":
    test_plotting_functions()
