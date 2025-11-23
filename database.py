"""Database operations using aiosqlite."""
import aiosqlite
from loguru import logger
from datetime import datetime
import os

from config import config


class Database:
    """Handles async SQLite database operations."""
    
    def __init__(self):
        self.db_path = config.DB_PATH
        self._ensure_directory()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _ensure_directory(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    async def initialize(self):
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Ticks table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    bid REAL,
                    ask REAL,
                    last REAL,
                    volume INTEGER,
                    high REAL,
                    low REAL,
                    close REAL
                )
            """)
            
            # Orders table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    order_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    submitted_at DATETIME NOT NULL,
                    filled_at DATETIME,
                    avg_fill_price REAL
                )
            """)
            
            # Trades table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    commission REAL,
                    pnl REAL,
                    timestamp DATETIME NOT NULL
                )
            """)
            
            # Daily PnL table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_pnl (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    realized_pnl REAL NOT NULL,
                    unrealized_pnl REAL,
                    total_pnl REAL NOT NULL
                )
            """)
            
            await db.commit()
            logger.info("Database tables initialized")
    
    async def insert_tick(self, symbol: str, data: dict):
        """Insert tick data."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO ticks (symbol, timestamp, bid, ask, last, volume, high, low, close)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                data.get('time', datetime.now()),
                data.get('bid'),
                data.get('ask'),
                data.get('last'),
                data.get('volume'),
                data.get('high'),
                data.get('low'),
                data.get('close')
            ))
            await db.commit()
    
    async def insert_order(self, order_id: str, symbol: str, action: str, 
                          quantity: int, order_type: str, status: str):
        """Insert order record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO orders (order_id, symbol, action, quantity, order_type, status, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_id, symbol, action, quantity, order_type, status, datetime.now()))
            await db.commit()
    
    async def update_order_status(self, order_id: str, status: str, 
                                  filled_at: datetime = None, avg_fill_price: float = None):
        """Update order status."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE orders 
                SET status = ?, filled_at = ?, avg_fill_price = ?
                WHERE order_id = ?
            """, (status, filled_at, avg_fill_price, order_id))
            await db.commit()
    
    async def insert_trade(self, order_id: str, symbol: str, action: str,
                          quantity: int, price: float, commission: float = 0, pnl: float = 0):
        """Insert trade record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO trades (order_id, symbol, action, quantity, price, commission, pnl, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, symbol, action, quantity, price, commission, pnl, datetime.now()))
            await db.commit()
