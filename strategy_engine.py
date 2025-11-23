"""Strategy engine for trading logic and signal generation."""
from typing import Dict, Optional
from loguru import logger
import pandas as pd
import numpy as np


class StrategyEngine:
    """Maintains strategy state and generates trading signals."""
    
    def __init__(self):
        self.positions = {}
        self.indicators = {}
        self.signals = []
        logger.info("Strategy engine initialized")
    
    def process_tick(self, symbol: str, data: dict) -> Optional[Dict]:
        """
        Process incoming tick data and generate signals.
        
        Args:
            symbol: Trading symbol
            data: Tick data dictionary
            
        Returns:
            Trading signal dict or None
        """
        # Update internal state
        if symbol not in self.indicators:
            self.indicators[symbol] = {
                'prices': [],
                'sma_fast': None,
                'sma_slow': None
            }
        
        # Store price
        self.indicators[symbol]['prices'].append(data['last'])
        prices = self.indicators[symbol]['prices']
        
        # Keep only last 100 prices
        if len(prices) > 100:
            prices.pop(0)
        
        # Calculate indicators if we have enough data
        if len(prices) >= 50:
            prices_array = np.array(prices)
            sma_fast = np.mean(prices_array[-20:])
            sma_slow = np.mean(prices_array[-50:])
            
            self.indicators[symbol]['sma_fast'] = sma_fast
            self.indicators[symbol]['sma_slow'] = sma_slow
            
            # Generate signal
            signal = self._generate_signal(symbol, sma_fast, sma_slow)
            if signal:
                logger.info(f"Generated signal for {symbol}: {signal}")
                return signal
        
        return None
    
    def _generate_signal(self, symbol: str, sma_fast: float, sma_slow: float) -> Optional[Dict]:
        """
        Generate trading signal based on moving average crossover.
        
        Args:
            symbol: Trading symbol
            sma_fast: Fast moving average
            sma_slow: Slow moving average
            
        Returns:
            Signal dictionary or None
        """
        current_position = self.positions.get(symbol, 0)
        
        # Buy signal: fast MA crosses above slow MA
        if sma_fast > sma_slow and current_position <= 0:
            return {
                'symbol': symbol,
                'action': 'BUY',
                'quantity': 100,
                'type': 'MARKET',
                'reason': 'SMA crossover bullish'
            }
        
        # Sell signal: fast MA crosses below slow MA
        elif sma_fast < sma_slow and current_position >= 0:
            return {
                'symbol': symbol,
                'action': 'SELL',
                'quantity': 100,
                'type': 'MARKET',
                'reason': 'SMA crossover bearish'
            }
        
        return None
    
    def update_position(self, symbol: str, quantity: int):
        """Update internal position tracking."""
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        logger.info(f"Updated position for {symbol}: {self.positions[symbol]}")
    
    def get_position(self, symbol: str) -> int:
        """Get current position for a symbol."""
        return self.positions.get(symbol, 0)
