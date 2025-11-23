"""Order execution and management."""
from typing import Dict, Optional
from loguru import logger
from ib_insync import IB, Stock, MarketOrder, LimitOrder

from config import config


class ExecutionEngine:
    """Handles order execution and tracking."""
    
    def __init__(self):
        self.ib = IB()
        self.orders = {}
        self.fills = []
        logger.info("Execution engine initialized")
    
    async def connect(self):
        """Connect to Interactive Brokers."""
        try:
            await self.ib.connectAsync(
                config.IB_HOST,
                config.IB_PORT,
                clientId=config.IB_CLIENT_ID + 1  # Different client ID
            )
            logger.info("Execution engine connected to IB")
        except Exception as e:
            logger.error(f"Failed to connect execution engine: {e}")
    
    async def execute_order(self, signal: Dict) -> Optional[str]:
        """
        Execute trading order based on signal.
        
        Args:
            signal: Trading signal dictionary
            
        Returns:
            Order ID or None if failed
        """
        try:
            # Create contract
            contract = Stock(signal['symbol'], 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Create order
            action = signal['action']
            quantity = signal['quantity']
            
            if signal['type'] == 'MARKET':
                order = MarketOrder(action, quantity)
            elif signal['type'] == 'LIMIT':
                order = LimitOrder(action, quantity, signal.get('limit_price'))
            else:
                logger.error(f"Unknown order type: {signal['type']}")
                return None
            
            # Submit order
            trade = self.ib.placeOrder(contract, order)
            order_id = str(trade.order.orderId)
            
            self.orders[order_id] = {
                'trade': trade,
                'signal': signal,
                'status': 'SUBMITTED'
            }
            
            logger.info(f"Order submitted: {order_id} - {action} {quantity} {signal['symbol']}")
            return order_id
            
        except Exception as e:
            logger.error(f"Failed to execute order: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id not in self.orders:
            logger.warning(f"Order not found: {order_id}")
            return False
        
        try:
            trade = self.orders[order_id]['trade']
            self.ib.cancelOrder(trade.order)
            self.orders[order_id]['status'] = 'CANCELLED'
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get status of an order."""
        if order_id not in self.orders:
            return None
        
        order_info = self.orders[order_id]
        trade = order_info['trade']
        
        return {
            'order_id': order_id,
            'status': trade.orderStatus.status,
            'filled': trade.orderStatus.filled,
            'remaining': trade.orderStatus.remaining,
            'avg_fill_price': trade.orderStatus.avgFillPrice
        }
    
    async def reconcile_positions(self) -> Dict:
        """
        Reconcile broker positions with internal tracking.
        
        Returns:
            Dictionary of discrepancies
        """
        positions = self.ib.positions()
        broker_positions = {
            pos.contract.symbol: pos.position 
            for pos in positions
        }
        
        logger.info(f"Reconciled {len(broker_positions)} positions with broker")
        return broker_positions
    
    def on_fill(self, trade):
        """Callback for order fills."""
        fill_info = {
            'order_id': trade.order.orderId,
            'symbol': trade.contract.symbol,
            'action': trade.order.action,
            'quantity': trade.orderStatus.filled,
            'price': trade.orderStatus.avgFillPrice,
            'time': trade.log[-1].time if trade.log else None
        }
        
        self.fills.append(fill_info)
        logger.info(f"Order filled: {fill_info}")
