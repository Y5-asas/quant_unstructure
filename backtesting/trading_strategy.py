#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Strategy Implementation
Implements sentiment-based trading strategy with quarterly rebalancing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import yfinance as yf
from dataclasses import dataclass


@dataclass
class TradingSignal:
    """Trading signal data structure"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    sentiment_score: float
    order_value: float
    timestamp: datetime


@dataclass
class PortfolioPosition:
    """Portfolio position data structure"""
    symbol: str
    shares: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float


class SentimentTradingStrategy:
    """Sentiment-based trading strategy with quarterly rebalancing"""
    
    def __init__(self, 
                 initial_capital: float = 300000.0,
                 order_value: float = 10000.0,
                 buy_signal_threshold: float = 60.0,
                 sell_signal_threshold: float = 40.0,
                 commission_rate: float = 0.0005,
                 top_k: Optional[int] = None):
        """
        Initialize trading strategy
        
        Args:
            initial_capital: Initial capital amount
            order_value: Fixed order value per trade
            buy_signal_threshold: Sentiment threshold for buy signals
            sell_signal_threshold: Sentiment threshold for sell signals
            commission_rate: Commission rate (0.05% = 0.0005)
            top_k: If specified, only trade top K positive/negative sentiment stocks
        """
        self.initial_capital = initial_capital
        self.order_value = order_value
        self.buy_signal_threshold = buy_signal_threshold
        self.sell_signal_threshold = sell_signal_threshold
        self.commission_rate = commission_rate
        self.top_k = top_k
        
        # Portfolio state
        self.cash = initial_capital
        self.positions: Dict[str, PortfolioPosition] = {}
        self.portfolio_history: List[Dict] = []
        
        # Dow Jones 30 symbols
        self.dow30_symbols = [
            'AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CSCO', 'CVX', 'DIS', 'DOW',
            'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD',
            'MMM', 'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'V', 'VZ',
            'WBA', 'WMT', 'XOM'
        ]
    
    def generate_trading_signals(self, sentiment_scores: Dict[str, float], 
                                timestamp: datetime) -> List[TradingSignal]:
        """
        Generate trading signals based on sentiment scores
        
        Args:
            sentiment_scores: Dict mapping symbol -> sentiment score
            timestamp: Signal generation timestamp
            
        Returns:
            List of trading signals
        """
        signals = []
        
        if self.top_k is None:
            # Original strategy: use threshold-based signals
            for symbol, sentiment_score in sentiment_scores.items():
                if symbol not in self.dow30_symbols:
                    continue
                    
                # Determine signal type based on sentiment score
                if sentiment_score >= self.buy_signal_threshold:
                    signal_type = 'BUY'
                elif sentiment_score <= self.sell_signal_threshold:
                    signal_type = 'SELL'
                else:
                    signal_type = 'NEUTRAL'
                
                # Create signal
                signal = TradingSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    sentiment_score=sentiment_score,
                    order_value=self.order_value,
                    timestamp=timestamp
                )
                signals.append(signal)
        else:
            # Top-K strategy: select top K positive and top K negative sentiment stocks
            valid_scores = {symbol: score for symbol, score in sentiment_scores.items() 
                           if symbol in self.dow30_symbols}
            
            if len(valid_scores) >= self.top_k * 2:
                # Sort by sentiment score
                sorted_scores = sorted(valid_scores.items(), key=lambda x: x[1], reverse=True)
                
                # Top K positive sentiment stocks (BUY signals)
                top_positive = sorted_scores[:self.top_k]
                # Top K negative sentiment stocks (SELL signals)
                top_negative = sorted_scores[-self.top_k:]
                
                # Create BUY signals for top positive sentiment stocks
                for symbol, sentiment_score in top_positive:
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type='BUY',
                        sentiment_score=sentiment_score,
                        order_value=self.order_value,
                        timestamp=timestamp
                    )
                    signals.append(signal)
                
                # Create SELL signals for top negative sentiment stocks
                for symbol, sentiment_score in top_negative:
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type='SELL',
                        sentiment_score=sentiment_score,
                        order_value=self.order_value,
                        timestamp=timestamp
                    )
                    signals.append(signal)
        
        return signals
    
    def execute_signals(self, signals: List[TradingSignal], 
                       prices: Dict[str, float]) -> Dict[str, float]:
        """
        Execute trading signals and update portfolio
        
        Args:
            signals: List of trading signals
            prices: Dict mapping symbol -> current price
            
        Returns:
            Dict of trade execution results
        """
        execution_results = {}
        
        # Group signals by type
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        neutral_signals = [s for s in signals if s.signal_type == 'NEUTRAL']
        
        # Execute buy signals first
        for signal in buy_signals:
            if signal.symbol in prices and not pd.isna(prices[signal.symbol]) and prices[signal.symbol] > 0:
                result = self._execute_buy_order(signal, prices[signal.symbol])
                execution_results[signal.symbol] = result
            else:
                execution_results[signal.symbol] = {
                    'success': False, 
                    'reason': f'Invalid price: {prices.get(signal.symbol, "N/A")}'
                }
        
        # Close positions for neutral signals
        for signal in neutral_signals:
            if signal.symbol in self.positions:
                result = self._close_position(signal.symbol, prices.get(signal.symbol, 0))
                execution_results[signal.symbol] = result
        
        # Execute sell signals (short selling if not in portfolio)
        for signal in sell_signals:
            if signal.symbol in prices and not pd.isna(prices[signal.symbol]) and prices[signal.symbol] > 0:
                if signal.symbol in self.positions:
                    # Close existing position
                    result = self._close_position(signal.symbol, prices[signal.symbol])
                else:
                    # Short selling (simplified - just mark as short)
                    result = self._execute_sell_order(signal, prices[signal.symbol])
                execution_results[signal.symbol] = result
            else:
                execution_results[signal.symbol] = {
                    'success': False, 
                    'reason': f'Invalid price: {prices.get(signal.symbol, "N/A")}'
                }
        
        return execution_results
    
    def _execute_buy_order(self, signal: TradingSignal, price: float) -> Dict:
        """
        Execute buy order
        
        Args:
            signal: Buy signal
            price: Current stock price
            
        Returns:
            Dict with execution details
        """
        if price <= 0:
            return {'success': False, 'reason': 'Invalid price'}
        
        # Calculate shares to buy
        gross_value = signal.order_value
        commission = gross_value * self.commission_rate
        net_value = gross_value - commission
        
        if net_value > self.cash:
            return {'success': False, 'reason': 'Insufficient cash'}
        
        shares = net_value / price
        
        # Update portfolio
        if signal.symbol in self.positions:
            # Add to existing position
            existing_pos = self.positions[signal.symbol]
            total_shares = existing_pos.shares + shares
            total_cost = existing_pos.cost_basis + net_value
            avg_cost = total_cost / total_shares
            
            self.positions[signal.symbol] = PortfolioPosition(
                symbol=signal.symbol,
                shares=total_shares,
                market_value=total_shares * price,
                cost_basis=total_cost,
                unrealized_pnl=(total_shares * price) - total_cost
            )
        else:
            # New position
            self.positions[signal.symbol] = PortfolioPosition(
                symbol=signal.symbol,
                shares=shares,
                market_value=shares * price,
                cost_basis=net_value,
                unrealized_pnl=(shares * price) - net_value
            )
        
        # Update cash
        self.cash -= net_value
        
        return {
            'success': True,
            'action': 'BUY',
            'shares': shares,
            'price': price,
            'value': net_value,
            'commission': commission
        }
    
    def _execute_sell_order(self, signal: TradingSignal, price: float) -> Dict:
        """
        Execute sell order (simplified short selling)
        
        Args:
            signal: Sell signal
            price: Current stock price
            
        Returns:
            Dict with execution details
        """
        if price <= 0:
            return {'success': False, 'reason': 'Invalid price'}
        
        # Simplified short selling - just record the signal
        # In practice, this would involve borrowing shares and selling them
        
        return {
            'success': True,
            'action': 'SELL_SHORT',
            'price': price,
            'value': signal.order_value,
            'note': 'Short position recorded'
        }
    
    def _close_position(self, symbol: str, price: float) -> Dict:
        """
        Close existing position
        
        Args:
            symbol: Stock symbol
            price: Current stock price
            
        Returns:
            Dict with execution details
        """
        if symbol not in self.positions:
            return {'success': False, 'reason': 'No position to close'}
        
        position = self.positions[symbol]
        
        if price <= 0:
            return {'success': False, 'reason': 'Invalid price'}
        
        # Calculate proceeds
        gross_proceeds = position.shares * price
        commission = gross_proceeds * self.commission_rate
        net_proceeds = gross_proceeds - commission
        
        # Calculate realized P&L
        realized_pnl = net_proceeds - position.cost_basis
        
        # Update cash
        self.cash += net_proceeds
        
        # Remove position
        del self.positions[symbol]
        
        return {
            'success': True,
            'action': 'CLOSE',
            'shares': position.shares,
            'price': price,
            'proceeds': net_proceeds,
            'realized_pnl': realized_pnl,
            'commission': commission
        }
    
    def update_portfolio_values(self, prices: Dict[str, float]) -> None:
        """
        Update portfolio position values with current prices
        
        Args:
            prices: Dict mapping symbol -> current price
        """
        for symbol, position in self.positions.items():
            if symbol in prices and not pd.isna(prices[symbol]) and prices[symbol] > 0:
                position.market_value = position.shares * prices[symbol]
                position.unrealized_pnl = position.market_value - position.cost_basis
            else:
                # If price is invalid, keep previous market value
                print(f"    ⚠️ {symbol}: Invalid price {prices.get(symbol, 'N/A')}, keeping previous market value")
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get current portfolio summary
        
        Returns:
            Dict with portfolio summary
        """
        total_market_value = sum(pos.market_value for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_portfolio_value = self.cash + total_market_value
        
        return {
            'cash': self.cash,
            'total_market_value': total_market_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_portfolio_value': total_portfolio_value,
            'num_positions': len(self.positions),
            'positions': {symbol: {
                'shares': pos.shares,
                'market_value': pos.market_value,
                'cost_basis': pos.cost_basis,
                'unrealized_pnl': pos.unrealized_pnl
            } for symbol, pos in self.positions.items()}
        }
    
    def record_portfolio_state(self, timestamp: datetime) -> None:
        """
        Record current portfolio state for backtesting
        
        Args:
            timestamp: Record timestamp
        """
        summary = self.get_portfolio_summary()
        summary['timestamp'] = timestamp
        self.portfolio_history.append(summary)
    
    def reset_portfolio(self) -> None:
        """Reset portfolio to initial state"""
        self.cash = self.initial_capital
        self.positions.clear()
        self.portfolio_history.clear()


def test_trading_strategy():
    """Test the trading strategy with sample data"""
    print("🚀 Testing Trading Strategy...")
    
    # Initialize strategy
    strategy = SentimentTradingStrategy()
    
    # Sample sentiment scores
    sentiment_scores = {
        'AAPL': 75.0,  # Buy signal
        'MSFT': 65.0,  # Buy signal
        'GOOGL': 35.0,  # Sell signal
        'TSLA': 45.0,   # Neutral signal
        'AMZN': 85.0    # Buy signal
    }
    
    # Sample prices
    prices = {
        'AAPL': 150.0,
        'MSFT': 300.0,
        'GOOGL': 2500.0,
        'TSLA': 800.0,
        'AMZN': 3200.0
    }
    
    # Generate signals
    timestamp = datetime.now()
    signals = strategy.generate_trading_signals(sentiment_scores, timestamp)
    
    print(f"📊 Generated {len(signals)} signals:")
    for signal in signals:
        print(f"  {signal.symbol}: {signal.signal_type} (score: {signal.sentiment_score:.1f})")
    
    # Execute signals
    results = strategy.execute_signals(signals, prices)
    
    print(f"\n💰 Execution results:")
    for symbol, result in results.items():
        print(f"  {symbol}: {result}")
    
    # Get portfolio summary
    summary = strategy.get_portfolio_summary()
    print(f"\n📈 Portfolio summary:")
    print(f"  Cash: ${summary['cash']:,.2f}")
    print(f"  Market value: ${summary['total_market_value']:,.2f}")
    print(f"  Total value: ${summary['total_portfolio_value']:,.2f}")
    print(f"  Positions: {summary['num_positions']}")
    
    print("✅ Trading strategy test completed!")


if __name__ == "__main__":
    test_trading_strategy()
