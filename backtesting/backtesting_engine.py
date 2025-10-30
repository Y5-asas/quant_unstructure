#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtesting Engine
Implements quarterly backtesting for sentiment-based trading strategy
"""

import pandas as pd
import numpy as np
try:
    import yfinance as yf
except ImportError:
    print("Warning: yfinance not installed. Install with: pip install yfinance")
    yf = None
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

os.environ['HF_HOME'] = "/root/autodl-tmp/huggingface_cache"
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
os.environ['HF_HUB_DISABLE_TELEMETRY'] = "1"
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = "1000"
from pathlib import Path

from sentiment_analyzer import FinancialSentimentAnalyzer
from trading_strategy import SentimentTradingStrategy


class BacktestingEngine:
    """Backtesting engine for quarterly sentiment-based trading"""
    
    def __init__(self, 
                 data_dir: str = "/root/quant/data/dogs_of_30_mdna",
                 start_date: str = "2020-01-01",
                 end_date: str = "2024-12-31",
                 top_k: Optional[int] = None,
                 sentiment_analyzer_type: str = "fingpt"):
        """
        Initialize backtesting engine
        
        Args:
            data_dir: Directory containing financial reports
            start_date: Backtesting start date
            end_date: Backtesting end date
            top_k: Number of top stocks for Top-K strategy
            sentiment_analyzer_type: Type of sentiment analyzer ("fingpt" or "deepseek")
        """
        self.data_dir = data_dir
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.sentiment_analyzer_type = sentiment_analyzer_type
        
        # Initialize components
        if sentiment_analyzer_type == "deepseek":
            from sentiment_analyzer_deepseek import DeepSeekSentimentAnalyzer
            self.sentiment_analyzer = DeepSeekSentimentAnalyzer()
        else:
            self.sentiment_analyzer = FinancialSentimentAnalyzer()
        self.strategy = SentimentTradingStrategy(top_k=top_k)
        
        # Data storage
        self.sentiment_data: Dict[str, Dict[str, float]] = {}
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.backtest_results: List[Dict] = []
        
        # Updated Dow Jones 30 symbols (as of 2024)
        # Removed: WBA (Walgreens), XOM (Exxon Mobil)
        # Added: AMZN (Amazon), CRM (Salesforce)
        self.dow30_symbols = [
            'AAPL', 'AMGN', 'AMZN', 'AXP', 'BA', 'CAT', 'CSCO', 'CVX', 'CRM', 'DIS', 
            'DOW', 'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 
            'MMM', 'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'V', 'VZ', 'WMT'
        ]
    
    def load_sentiment_data(self) -> bool:
        """
        Load and process sentiment data from financial reports
        
        Returns:
            bool: Success status
        """
        print("📊 Loading sentiment data...")
        
        # Load the sentiment model (only for FinGPT, DeepSeek uses API)
        if hasattr(self.sentiment_analyzer, 'load_model'):
            if not self.sentiment_analyzer.load_model():
                print("❌ Failed to load sentiment model")
                return False
        else:
            # For API-based analyzers like DeepSeek, test connection instead
            if hasattr(self.sentiment_analyzer, 'test_api_connection'):
                if not self.sentiment_analyzer.test_api_connection():
                    print("❌ Failed to connect to sentiment analysis API")
                    return False
            print("✅ API-based sentiment analyzer ready")
        
        # Process financial reports
        try:
            # Use cache file for DeepSeek analyzer
            cache_file = None
            if hasattr(self.sentiment_analyzer, 'cache_file'):
                cache_file = f"/root/quant/backtesting/sentiment_cache_{self.sentiment_analyzer_type}.json"
            
            if hasattr(self.sentiment_analyzer, 'process_financial_reports'):
                if cache_file and hasattr(self.sentiment_analyzer, 'process_financial_reports'):
                    self.sentiment_data = self.sentiment_analyzer.process_financial_reports(self.data_dir, cache_file)
                else:
                    self.sentiment_data = self.sentiment_analyzer.process_financial_reports(self.data_dir)
            else:
                # Fallback for older analyzers
                self.sentiment_data = self.sentiment_analyzer.process_financial_reports(self.data_dir)
            
            print(f"✅ Loaded sentiment data for {len(self.sentiment_data)} companies")
            return True
        except Exception as e:
            print(f"❌ Failed to load sentiment data: {e}")
            return False
    
    def load_price_data(self) -> bool:
        """
        Load historical price data from local CSV files for Dow Jones 30 stocks
        
        Returns:
            bool: Success status
        """
        print("📈 Loading price data from local CSV files...")
        
        # Path to the real price data
        price_data_dir = "/root/quant/quant_rl/data/DJI_data"
        
        try:
            successful_loads = 0
            
            for symbol in self.dow30_symbols:
                csv_file = f"{price_data_dir}/{symbol}.csv"
                
                if os.path.exists(csv_file):
                    try:
                        # Load CSV data
                        df = pd.read_csv(csv_file)
                        
                        # Convert date column to datetime and set as index
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        
                        # Filter data for the backtesting period
                        df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
                        
                        # Rename columns to match expected format
                        df = df.rename(columns={
                            'open': 'Open',
                            'high': 'High', 
                            'low': 'Low',
                            'close': 'Close',
                            'volume': 'Volume'
                        })
                        
                        # Keep only the required columns
                        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        df = df[required_columns]
                        
                        # Remove any rows with missing data
                        df = df.dropna()
                        
                        if len(df) > 0:
                            self.price_data[symbol] = df
                            print(f"    ✅ {symbol}: {len(df)} days loaded from CSV")
                            successful_loads += 1
                        else:
                            print(f"    ⚠️ {symbol}: No data in specified date range")
                            
                    except Exception as e:
                        print(f"    ❌ {symbol}: Failed to load CSV - {e}")
                else:
                    print(f"    ⚠️ {symbol}: CSV file not found at {csv_file}")
            
            if successful_loads > 0:
                print(f"✅ Loaded price data for {successful_loads}/{len(self.dow30_symbols)} stocks")
                print(f"📅 Date range: {self.start_date.date()} to {self.end_date.date()}")
                return True
            else:
                print("❌ Failed to load any price data")
                return False
            
        except Exception as e:
            print(f"❌ Failed to load price data: {e}")
            return False
    
    def get_quarterly_periods(self) -> List[Tuple[datetime, datetime]]:
        """
        Generate quarterly periods for backtesting
        
        Returns:
            List of (start_date, end_date) tuples
        """
        periods = []
        current_date = self.start_date
        
        while current_date < self.end_date:
            # Calculate quarter start
            year = current_date.year
            quarter = ((current_date.month - 1) // 3) + 1
            quarter_start = datetime(year, (quarter - 1) * 3 + 1, 1)
            
            # Calculate quarter end
            if quarter == 4:
                quarter_end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                quarter_end = datetime(year, quarter * 3 + 1, 1) - timedelta(days=1)
            
            # Ensure we don't exceed end date
            quarter_end = min(quarter_end, self.end_date)
            
            periods.append((quarter_start, quarter_end))
            
            # Move to next quarter
            current_date = quarter_end + timedelta(days=1)
        
        return periods
    
    def get_sentiment_for_period(self, period_start: datetime, period_end: datetime) -> Dict[str, float]:
        """
        Get sentiment scores for a specific period
        
        Args:
            period_start: Period start date
            period_end: Period end date
            
        Returns:
            Dict mapping symbol -> sentiment score
        """
        period_scores = {}
        target_quarter = f"{period_start.year}_Q{((period_start.month - 1) // 3) + 1}"
        
        for symbol in self.dow30_symbols:
            if symbol in self.sentiment_data:
                # Look for sentiment data for this quarter
                if target_quarter in self.sentiment_data[symbol]:
                    period_scores[symbol] = self.sentiment_data[symbol][target_quarter]
                else:
                    # Use neutral score if no data available
                    period_scores[symbol] = 50.0
            else:
                period_scores[symbol] = 50.0
        
        return period_scores
    
    def get_prices_for_date(self, date: datetime) -> Dict[str, float]:
        """
        Get stock prices for a specific date
        
        Args:
            date: Target date
            
        Returns:
            Dict mapping symbol -> price
        """
        prices = {}
        
        for symbol in self.dow30_symbols:
            if symbol in self.price_data:
                # Find the closest trading day
                hist_data = self.price_data[symbol]
                
                # Look for exact date first
                if date.date() in hist_data.index.date:
                    price = hist_data.loc[hist_data.index.date == date.date(), 'Close'].iloc[0]
                else:
                    # Find the closest previous trading day
                    available_dates = hist_data.index[hist_data.index.date <= date.date()]
                    if len(available_dates) > 0:
                        closest_date = available_dates[-1]
                        price = hist_data.loc[closest_date, 'Close']
                    else:
                        # If no previous date, try to find the next available date
                        future_dates = hist_data.index[hist_data.index.date > date.date()]
                        if len(future_dates) > 0:
                            closest_date = future_dates[0]
                            price = hist_data.loc[closest_date, 'Close']
                        else:
                            # If no data available, skip this stock
                            print(f"    ⚠️ {symbol}: No price data available for {date.date()}")
                            continue
                
                prices[symbol] = price
            else:
                prices[symbol] = np.nan
        
        return prices
    
    def calculate_buy_and_hold_returns(self) -> pd.DataFrame:
        """
        Calculate buy-and-hold returns for comparison
        Equal-weighted portfolio of all Dow Jones 30 stocks
        
        Returns:
            DataFrame with buy-and-hold performance
        """
        print("📊 Calculating buy-and-hold returns...")
        
        periods = self.get_quarterly_periods()
        bh_results = []
        
        # Initial portfolio value (same as sentiment strategy)
        initial_capital = 300000
        portfolio_value = initial_capital
        
        for i, (period_start, period_end) in enumerate(periods):
            # Get prices at start and end of period
            start_prices = self.get_prices_for_date(period_start)
            end_prices = self.get_prices_for_date(period_end)
            
            if i == 0:
                # First period: calculate initial portfolio value
                valid_stocks = []
                for symbol in self.dow30_symbols:
                    if (symbol in start_prices and not np.isnan(start_prices[symbol]) 
                        and start_prices[symbol] > 0):
                        valid_stocks.append(symbol)
                
                if valid_stocks:
                    # Equal weight allocation
                    weight_per_stock = 1.0 / len(valid_stocks)
                    shares_per_stock = {}
                    for symbol in valid_stocks:
                        shares_per_stock[symbol] = (portfolio_value * weight_per_stock) / start_prices[symbol]
                    
                    # Calculate portfolio value at end of period
                    end_portfolio_value = 0
                    for symbol in valid_stocks:
                        if symbol in end_prices and not np.isnan(end_prices[symbol]):
                            end_portfolio_value += shares_per_stock[symbol] * end_prices[symbol]
                    
                    if end_portfolio_value > 0:
                        period_return = (end_portfolio_value - portfolio_value) / portfolio_value
                        portfolio_value = end_portfolio_value
                    else:
                        period_return = 0
                else:
                    period_return = 0
            else:
                # Subsequent periods: calculate return based on price changes
                valid_stocks = []
                price_changes = []
                
                for symbol in self.dow30_symbols:
                    if (symbol in start_prices and symbol in end_prices and 
                        not np.isnan(start_prices[symbol]) and not np.isnan(end_prices[symbol])
                        and start_prices[symbol] > 0 and end_prices[symbol] > 0):
                        
                        price_change = (end_prices[symbol] - start_prices[symbol]) / start_prices[symbol]
                        price_changes.append(price_change)
                        valid_stocks.append(symbol)
                
                if price_changes:
                    # Equal-weighted average return
                    period_return = np.mean(price_changes)
                    portfolio_value = portfolio_value * (1 + period_return)
                else:
                    period_return = 0
            
            # Calculate cumulative return
            cumulative_return = (portfolio_value - initial_capital) / initial_capital
            
            bh_results.append({
                'period_start': period_start,
                'period_end': period_end,
                'quarter': f"{period_start.year}_Q{((period_start.month - 1) // 3) + 1}",
                'return': period_return,
                'cumulative_return': cumulative_return,
                'portfolio_value': portfolio_value
            })
        
        return pd.DataFrame(bh_results)
    
    def run_backtest(self) -> Dict:
        """
        Run the complete backtesting simulation
        
        Returns:
            Dict with backtesting results
        """
        print("🚀 Starting backtesting simulation...")
        
        # Load required data (skip if sentiment data already loaded)
        if not self.sentiment_data:
            if not self.load_sentiment_data():
                return {'error': 'Failed to load sentiment data'}
        else:
            print("✅ Using preloaded sentiment data")
        
        if not self.load_price_data():
            return {'error': 'Failed to load price data'}
        
        # Get quarterly periods
        periods = self.get_quarterly_periods()
        print(f"📅 Backtesting {len(periods)} quarters from {self.start_date.date()} to {self.end_date.date()}")
        
        # Reset strategy
        self.strategy.reset_portfolio()
        
        # Run backtest for each quarter
        for i, (period_start, period_end) in enumerate(periods):
            quarter = f"{period_start.year}_Q{((period_start.month - 1) // 3) + 1}"
            print(f"\n📊 Processing {quarter} ({period_start.date()} to {period_end.date()})")
            
            # Get sentiment scores for this period
            sentiment_scores = self.get_sentiment_for_period(period_start, period_end)
            
            # Generate trading signals
            signals = self.strategy.generate_trading_signals(sentiment_scores, period_start)
            
            # Get prices for signal execution
            execution_prices = self.get_prices_for_date(period_start)
            
            # Execute signals
            execution_results = self.strategy.execute_signals(signals, execution_prices)
            
            # Update portfolio values at period end
            end_prices = self.get_prices_for_date(period_end)
            self.strategy.update_portfolio_values(end_prices)
            
            # Record portfolio state
            self.strategy.record_portfolio_state(period_end)
            
            # Store results
            period_result = {
                'quarter': quarter,
                'period_start': period_start,
                'period_end': period_end,
                'sentiment_scores': sentiment_scores,
                'signals': len(signals),
                'execution_results': execution_results,
                'portfolio_summary': self.strategy.get_portfolio_summary()
            }
            self.backtest_results.append(period_result)
            
            # Print summary
            portfolio = self.strategy.get_portfolio_summary()
            total_return = (portfolio['total_portfolio_value'] / self.strategy.initial_capital - 1) * 100
            print(f"  💰 Portfolio value: ${portfolio['total_portfolio_value']:,.2f} ({total_return:+.2f}%)")
            print(f"  📈 Positions: {portfolio['num_positions']}, Cash: ${portfolio['cash']:,.2f}")
        
        # Calculate buy-and-hold comparison
        bh_results = self.calculate_buy_and_hold_returns()
        
        # Compile final results
        final_results = {
            'strategy_performance': self.backtest_results,
            'buy_and_hold': bh_results,
            'final_portfolio': self.strategy.get_portfolio_summary(),
            'periods_tested': len(periods),
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        
        print(f"\n✅ Backtesting completed!")
        print(f"📊 Tested {len(periods)} quarters")
        
        return final_results
    
    def save_results(self, results: Dict, output_dir: str = "/root/quant/backtesting/results") -> None:
        """
        Save backtesting results to files
        
        Args:
            results: Backtesting results
            output_dir: Output directory
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save strategy performance
        strategy_df = pd.DataFrame([
            {
                'quarter': r['quarter'],
                'period_start': r['period_start'],
                'period_end': r['period_end'],
                'signals': r['signals'],
                'portfolio_value': r['portfolio_summary']['total_portfolio_value'],
                'cash': r['portfolio_summary']['cash'],
                'positions': r['portfolio_summary']['num_positions']
            }
            for r in results['strategy_performance']
        ])
        
        strategy_df.to_csv(f"{output_dir}/strategy_performance.csv", index=False)
        
        # Save buy-and-hold results
        if not results['buy_and_hold'].empty:
            results['buy_and_hold'].to_csv(f"{output_dir}/buy_and_hold.csv", index=False)
        
        print(f"💾 Results saved to {output_dir}")


def test_backtesting_engine():
    """Test the backtesting engine"""
    print("🚀 Testing Backtesting Engine...")
    
    # Initialize engine
    engine = BacktestingEngine(
        start_date="2020-01-01",
        end_date="2021-12-31"  # Shorter period for testing
    )
    
    # Run backtest
    results = engine.run_backtest()
    
    if 'error' in results:
        print(f"❌ Backtesting failed: {results['error']}")
        return
    
    # Print summary
    final_portfolio = results['final_portfolio']
    total_return = (final_portfolio['total_portfolio_value'] / 300000 - 1) * 100
    
    print(f"\n📊 Final Results:")
    print(f"  Portfolio value: ${final_portfolio['total_portfolio_value']:,.2f}")
    print(f"  Total return: {total_return:+.2f}%")
    print(f"  Positions: {final_portfolio['num_positions']}")
    print(f"  Cash: ${final_portfolio['cash']:,.2f}")
    
    print("✅ Backtesting engine test completed!")


if __name__ == "__main__":
    test_backtesting_engine()
