"""Data ingestion module for real-time and historical market data."""
import asyncio
from typing import Optional, Callable
from loguru import logger
from ib_insync import IB, Stock, util
import pandas as pd

from config import config
from database import Database


class DataIngestion:
    """Handles market data ingestion from Interactive Brokers."""
    
    def __init__(self):
        self.ib = IB()
        self.db = Database()
        self.subscriptions = {}
        self._callbacks = []
        self._reconnect_task = None
        self._is_running = True
        
    async def connect(self) -> bool:
        """Connect to Interactive Brokers with auto-reconnect."""
        attempt = 0
        while attempt < config.MAX_RECONNECT_ATTEMPTS and self._is_running:
            try:
                await self.ib.connectAsync(
                    config.IB_HOST,
                    config.IB_PORT,
                    clientId=config.IB_CLIENT_ID
                )
                mode = "PAPER" if config.IB_PORT == 7497 else "LIVE"
                logger.info(f"Connected to IB at {config.IB_HOST}:{config.IB_PORT} ({mode} mode)")
                
                # Setup disconnect handler
                self.ib.disconnectedEvent += self._on_disconnect
                return True
                
            except Exception as e:
                attempt += 1
                logger.error(f"Connection attempt {attempt}/{config.MAX_RECONNECT_ATTEMPTS} failed: {e}")
                
                if attempt < config.MAX_RECONNECT_ATTEMPTS:
                    delay = config.RECONNECT_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.critical("Max reconnection attempts reached")
                    return False
        
        return False
    
    def _on_disconnect(self):
        """Handle unexpected disconnection."""
        if self._is_running:
            logger.warning("IB connection lost - attempting to reconnect")
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._reconnect())
    
    async def _reconnect(self):
        """Attempt to reconnect after disconnect."""
        await asyncio.sleep(config.RECONNECT_DELAY)
        success = await self.connect()
        
        if success:
            logger.info("Reconnection successful")
            # Re-subscribe to tickers
            symbols = list(self.subscriptions.keys())
            self.subscriptions.clear()
            for symbol in symbols:
                logger.info(f"Re-subscribing to {symbol}")
                self.subscribe_ticker(symbol)
        else:
            logger.error("Reconnection failed")
    
    async def disconnect(self):
        """Disconnect from Interactive Brokers."""
        self._is_running = False
        if self.ib.isConnected():
            self.ib.disconnect()
            logger.info("Disconnected from IB")
    
    def subscribe_ticker(self, symbol: str, callback: Optional[Callable] = None):
        """Subscribe to real-time market data for a symbol."""
        contract = Stock(symbol, 'SMART', 'USD')
        self.ib.qualifyContracts(contract)
        
        ticker = self.ib.reqMktData(contract, '', False, False)
        self.subscriptions[symbol] = ticker
        
        if callback:
            ticker.updateEvent += lambda t: callback(self._ticker_to_dict(t))
        
        logger.info(f"Subscribed to {symbol}")
        return ticker
    
    def unsubscribe_ticker(self, symbol: str):
        """Unsubscribe from market data."""
        if symbol in self.subscriptions:
            self.ib.cancelMktData(self.subscriptions[symbol].contract)
            del self.subscriptions[symbol]
            logger.info(f"Unsubscribed from {symbol}")
    
    async def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "1 min"
    ) -> pd.DataFrame:
        """Fetch historical data and return as DataFrame."""
        contract = Stock(symbol, 'SMART', 'USD')
        self.ib.qualifyContracts(contract)
        
        bars = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow='TRADES',
            useRTH=True
        )
        
        df = util.df(bars)
        logger.info(f"Fetched {len(df)} bars for {symbol}")
        return df
    
    async def persist_tick(self, symbol: str, data: dict):
        """Persist tick data to database."""
        await self.db.insert_tick(symbol, data)
    
    @staticmethod
    def _ticker_to_dict(ticker) -> dict:
        """Convert ticker object to dictionary."""
        return {
            'time': ticker.time,
            'bid': ticker.bid,
            'ask': ticker.ask,
            'last': ticker.last,
            'volume': ticker.volume,
            'high': ticker.high,
            'low': ticker.low,
            'close': ticker.close
        }
