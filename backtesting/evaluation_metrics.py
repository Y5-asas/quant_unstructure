#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation Metrics Module
Calculates comprehensive performance metrics for backtesting results
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import scipy.stats as stats


class PerformanceMetrics:
    """Calculate comprehensive performance metrics for trading strategies"""
    
    def __init__(self):
        """Initialize performance metrics calculator"""
        pass
    
    def calculate_returns(self, portfolio_values: List[float], 
                         timestamps: List[datetime]) -> pd.DataFrame:
        """
        Calculate various return metrics
        
        Args:
            portfolio_values: List of portfolio values over time
            timestamps: List of corresponding timestamps
            
        Returns:
            DataFrame with return calculations
        """
        df = pd.DataFrame({
            'timestamp': timestamps,
            'portfolio_value': portfolio_values
        })
        
        # Calculate returns
        df['returns'] = df['portfolio_value'].pct_change(fill_method=None)
        df['log_returns'] = np.log(df['portfolio_value'] / df['portfolio_value'].shift(1))
        df['cumulative_return'] = (df['portfolio_value'] / df['portfolio_value'].iloc[0] - 1) * 100
        
        # Calculate compound returns (quarterly)
        df['compound_return'] = df['returns'].rolling(window=1).apply(
            lambda x: (1 + x).prod() - 1 if len(x) == 1 else np.nan
        )
        
        return df
    
    def calculate_annual_return(self, returns_df: pd.DataFrame) -> float:
        """
        Calculate annual return
        
        Args:
            returns_df: DataFrame with returns data
            
        Returns:
            Annual return percentage
        """
        if len(returns_df) < 2:
            return 0.0
        
        # Calculate total return over the period
        total_return = (returns_df['portfolio_value'].iloc[-1] / returns_df['portfolio_value'].iloc[0]) - 1
        
        # Calculate number of years
        start_date = returns_df['timestamp'].iloc[0]
        end_date = returns_df['timestamp'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        
        # Annualize the return
        if years > 0:
            annual_return = (1 + total_return) ** (1 / years) - 1
            return annual_return * 100
        
        return 0.0
    
    def calculate_annual_compound_return(self, returns_df: pd.DataFrame) -> float:
        """
        Calculate annual compound return
        
        Args:
            returns_df: DataFrame with returns data
            
        Returns:
            Annual compound return percentage
        """
        if len(returns_df) < 2:
            return 0.0
        
        # Calculate total compound return
        total_compound_return = (returns_df['portfolio_value'].iloc[-1] / returns_df['portfolio_value'].iloc[0]) - 1
        
        # Calculate number of years
        start_date = returns_df['timestamp'].iloc[0]
        end_date = returns_df['timestamp'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        
        # Annualize the compound return
        if years > 0:
            annual_compound_return = (1 + total_compound_return) ** (1 / years) - 1
            return annual_compound_return * 100
        
        return 0.0
    
    def calculate_annual_cumulative_return(self, returns_df: pd.DataFrame) -> float:
        """
        Calculate annual cumulative return
        
        Args:
            returns_df: DataFrame with returns data
            
        Returns:
            Annual cumulative return percentage
        """
        if len(returns_df) < 2:
            return 0.0
        
        # Calculate total cumulative return
        total_cumulative_return = returns_df['cumulative_return'].iloc[-1]
        
        # Calculate number of years
        start_date = returns_df['timestamp'].iloc[0]
        end_date = returns_df['timestamp'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        
        # Annualize the cumulative return
        if years > 0:
            annual_cumulative_return = total_cumulative_return / years
            return annual_cumulative_return
        
        return 0.0
    
    def calculate_sharpe_ratio(self, returns_df: pd.DataFrame, 
                              risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            returns_df: DataFrame with returns data
            risk_free_rate: Risk-free rate (default 2%)
            
        Returns:
            Sharpe ratio
        """
        if len(returns_df) < 2:
            return 0.0
        
        returns = returns_df['returns'].dropna()
        if len(returns) == 0:
            return 0.0
        
        # Calculate excess returns
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        
        # Calculate Sharpe ratio
        if returns.std() > 0:
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
            return sharpe_ratio
        
        return 0.0
    
    def calculate_sortino_ratio(self, returns_df: pd.DataFrame, 
                               risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sortino ratio
        
        Args:
            returns_df: DataFrame with returns data
            risk_free_rate: Risk-free rate (default 2%)
            
        Returns:
            Sortino ratio
        """
        if len(returns_df) < 2:
            return 0.0
        
        returns = returns_df['returns'].dropna()
        if len(returns) == 0:
            return 0.0
        
        # Calculate excess returns
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        
        # Calculate downside deviation
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) > 0:
            downside_deviation = downside_returns.std() * np.sqrt(252)
            if downside_deviation > 0:
                sortino_ratio = (excess_returns.mean() * 252) / downside_deviation
                return sortino_ratio
        
        return 0.0
    
    def calculate_calmar_ratio(self, returns_df: pd.DataFrame) -> float:
        """
        Calculate Calmar ratio
        
        Args:
            returns_df: DataFrame with returns data
            
        Returns:
            Calmar ratio
        """
        annual_return = self.calculate_annual_return(returns_df) / 100
        max_drawdown = self.calculate_max_drawdown(returns_df) / 100
        
        if abs(max_drawdown) > 0:
            calmar_ratio = annual_return / abs(max_drawdown)
            return calmar_ratio
        
        return 0.0
    
    def calculate_max_drawdown(self, returns_df: pd.DataFrame) -> float:
        """
        Calculate maximum drawdown
        
        Args:
            returns_df: DataFrame with returns data
            
        Returns:
            Maximum drawdown percentage
        """
        if len(returns_df) < 2:
            return 0.0
        
        portfolio_values = returns_df['portfolio_value']
        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak
        
        max_drawdown = drawdown.min() * 100
        return max_drawdown
    
    def calculate_annual_volatility(self, returns_df: pd.DataFrame) -> float:
        """
        Calculate annual volatility
        
        Args:
            returns_df: DataFrame with returns data
            
        Returns:
            Annual volatility percentage
        """
        if len(returns_df) < 2:
            return 0.0
        
        returns = returns_df['returns'].dropna()
        if len(returns) == 0:
            return 0.0
        
        # Annualize volatility
        annual_volatility = returns.std() * np.sqrt(252) * 100
        return annual_volatility
    
    def calculate_var(self, returns_df: pd.DataFrame, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            returns_df: DataFrame with returns data
            confidence_level: Confidence level (default 95%)
            
        Returns:
            VaR percentage
        """
        if len(returns_df) < 2:
            return 0.0
        
        returns = returns_df['returns'].dropna()
        if len(returns) == 0:
            return 0.0
        
        # Calculate VaR
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(returns, var_percentile) * 100
        
        return var
    
    def calculate_all_metrics(self, returns_df: pd.DataFrame, 
                            risk_free_rate: float = 0.02) -> Dict[str, float]:
        """
        Calculate all performance metrics
        
        Args:
            returns_df: DataFrame with returns data
            risk_free_rate: Risk-free rate
            
        Returns:
            Dictionary with all metrics
        """
        metrics = {
            'Annual Return': self.calculate_annual_return(returns_df),
            'Annual Compound Return': self.calculate_annual_compound_return(returns_df),
            'Annual Cumulative Return': self.calculate_annual_cumulative_return(returns_df),
            'Sharpe Ratio': self.calculate_sharpe_ratio(returns_df, risk_free_rate),
            'Sortino Ratio': self.calculate_sortino_ratio(returns_df, risk_free_rate),
            'Calmar Ratio': self.calculate_calmar_ratio(returns_df),
            'Max Drawdown (MDD)': self.calculate_max_drawdown(returns_df),
            'Annual Volatility': self.calculate_annual_volatility(returns_df),
            '95% Daily VaR': self.calculate_var(returns_df, 0.95)
        }
        
        return metrics
    
    def compare_strategies(self, strategy_returns: pd.DataFrame, 
                          buy_hold_returns: pd.DataFrame,
                          strategy_name: str = "Sentiment Strategy") -> pd.DataFrame:
        """
        Compare strategy performance with buy-and-hold
        
        Args:
            strategy_returns: Strategy returns DataFrame
            buy_hold_returns: Buy-and-hold returns DataFrame
            strategy_name: Name of the strategy
            
        Returns:
            Comparison DataFrame
        """
        # Calculate metrics for both strategies
        strategy_metrics = self.calculate_all_metrics(strategy_returns)
        buy_hold_metrics = self.calculate_all_metrics(buy_hold_returns)
        
        # Create comparison DataFrame
        comparison_df = pd.DataFrame({
            'Metrics': list(strategy_metrics.keys()),
            'Buy&Hold': [buy_hold_metrics[metric] for metric in strategy_metrics.keys()],
            strategy_name: [strategy_metrics[metric] for metric in strategy_metrics.keys()]
        })
        
        # Round values appropriately
        for col in ['Buy&Hold', strategy_name]:
            comparison_df[col] = comparison_df[col].round(2)
        
        return comparison_df
    
    def format_percentage_metrics(self, metrics_df: pd.DataFrame) -> pd.DataFrame:
        """
        Format metrics DataFrame with appropriate percentage formatting
        
        Args:
            metrics_df: Metrics DataFrame
            
        Returns:
            Formatted DataFrame
        """
        formatted_df = metrics_df.copy()
        
        # Metrics that should be displayed as percentages
        percentage_metrics = [
            'Annual Return', 'Annual Compound Return', 'Annual Cumulative Return',
            'Max Drawdown (MDD)', 'Annual Volatility', '95% Daily VaR'
        ]
        
        for metric in percentage_metrics:
            if metric in formatted_df['Metrics'].values:
                for col in formatted_df.columns[1:]:  # Skip 'Metrics' column
                    if col in formatted_df.columns:
                        formatted_df.loc[formatted_df['Metrics'] == metric, col] = \
                            formatted_df.loc[formatted_df['Metrics'] == metric, col].apply(
                                lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
                            )
        
        return formatted_df


def test_evaluation_metrics():
    """Test the evaluation metrics module"""
    print("🚀 Testing Evaluation Metrics...")
    
    # Create sample data
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Generate sample portfolio values with some trend and volatility
    returns = np.random.normal(0.001, 0.02, 100)  # 0.1% daily return, 2% volatility
    portfolio_values = [100000]
    for ret in returns[1:]:
        portfolio_values.append(portfolio_values[-1] * (1 + ret))
    
    # Create returns DataFrame
    returns_df = pd.DataFrame({
        'timestamp': dates,
        'portfolio_value': portfolio_values
    })
    
    # Initialize metrics calculator
    metrics_calc = PerformanceMetrics()
    
    # Calculate all metrics
    metrics = metrics_calc.calculate_all_metrics(returns_df)
    
    print("📊 Performance Metrics:")
    for metric, value in metrics.items():
        if 'Ratio' in metric:
            print(f"  {metric}: {value:.2f}")
        elif 'Return' in metric or 'Volatility' in metric or 'VaR' in metric or 'MDD' in metric:
            print(f"  {metric}: {value:.2f}%")
        else:
            print(f"  {metric}: {value:.2f}")
    
    print("✅ Evaluation metrics test completed!")


if __name__ == "__main__":
    test_evaluation_metrics()
