"""Risk management and position sizing."""
from typing import Dict, Optional
from loguru import logger
from datetime import datetime, date

from config import config


class RiskManager:
    """Manages risk limits and validates orders."""
    
    def __init__(self):
        self.daily_pnl = 0.0
        self.positions = {}
        self.current_date = date.today()
        self.circuit_breaker_active = False
        logger.info("Risk manager initialized")
    
    def validate_order(self, signal: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate order against risk limits.
        
        Args:
            signal: Trading signal dictionary
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check circuit breaker
        if self.circuit_breaker_active:
            return False, "Circuit breaker active"
        
        # Reset daily counters if new day
        if date.today() != self.current_date:
            self._reset_daily_counters()
        
        # Check daily loss limit
        if self.daily_pnl <= -config.DAILY_LOSS_LIMIT:
            self._activate_circuit_breaker()
            return False, f"Daily loss limit reached: ${self.daily_pnl:.2f}"
        
        # Check position size
        symbol = signal['symbol']
        quantity = signal['quantity']
        estimated_value = quantity * 100  # Simplified - should use actual price
        
        if estimated_value > config.MAX_POSITION_SIZE:
            return False, f"Position size ${estimated_value} exceeds limit ${config.MAX_POSITION_SIZE}"
        
        # Check leverage
        total_exposure = sum(abs(pos['value']) for pos in self.positions.values())
        if total_exposure > config.MAX_LEVERAGE * 100000:  # Simplified
            return False, f"Leverage limit exceeded"
        
        logger.info(f"Order validated for {symbol}")
        return True, None
    
    def update_pnl(self, pnl: float):
        """Update daily P&L."""
        self.daily_pnl += pnl
        logger.info(f"Daily P&L: ${self.daily_pnl:.2f}")
        
        # Check if we hit loss limit
        if self.daily_pnl <= -config.DAILY_LOSS_LIMIT:
            self._activate_circuit_breaker()
    
    def update_position(self, symbol: str, quantity: int, price: float):
        """Update position tracking."""
        if symbol not in self.positions:
            self.positions[symbol] = {'quantity': 0, 'value': 0.0}
        
        self.positions[symbol]['quantity'] += quantity
        self.positions[symbol]['value'] = self.positions[symbol]['quantity'] * price
        
        logger.info(f"Position updated - {symbol}: {self.positions[symbol]['quantity']} @ ${price}")
    
    def _activate_circuit_breaker(self):
        """Activate circuit breaker to stop trading."""
        self.circuit_breaker_active = True
        logger.critical("CIRCUIT BREAKER ACTIVATED - Trading halted")
    
    def _reset_daily_counters(self):
        """Reset daily counters for new trading day."""
        self.daily_pnl = 0.0
        self.current_date = date.today()
        self.circuit_breaker_active = False
        logger.info("Daily counters reset for new trading day")
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics."""
        return {
            'daily_pnl': self.daily_pnl,
            'circuit_breaker_active': self.circuit_breaker_active,
            'positions': self.positions,
            'total_exposure': sum(abs(pos['value']) for pos in self.positions.values())
        }
