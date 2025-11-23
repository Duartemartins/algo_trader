# Algorithmic Trading System Components

## Core Components

### 1. Data Ingestion
- Real time quotes via WebSocket
- Fallback to REST polling
- Persist to a local DB or at least CSV/parquet for audit

### 2. Strategy Engine
- Takes price stream
- Maintains internal state (positions, indicators)
- Emits "desired positions" or orders

### 3. Risk / Portfolio Layer
- Max exposure per instrument
- Max leverage
- Per day loss limit
- Circuit breaker that flattens and stops trading when thresholds hit

### 4. Execution
- Translates strategy intent to orders
- Handles order IDs, partial fills, errors
- Compares broker position with internal position and reconciles

### 5. Monitoring
- Logs to file and maybe a lightweight dashboard
- Alerts: email / Telegram / Signal when:
  - Orders fail
  - Portfolio drawdown > threshold
  - Process crashes or stops receiving data

## Implementation Stack

### Core Dependencies
- **ib_insync** - Interactive Brokers API client
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **aiosqlite** - Async SQLite database
- **pyarrow** - Parquet file format support

### API & Web
- **fastapi** - REST API framework
- **uvicorn** - ASGI server
- **requests** - HTTP client

### Utilities
- **schedule** - Task scheduling
- **python_dotenv** - Environment configuration
- **loguru** - Logging
- **rich** - Terminal output formatting
- **matplotlib** - Data visualization
- **twilio** - WhatsApp alerts

---

## Project Structure

### Core Modules

#### `main.py`
Entry point for the trading system. Initializes all components, manages the main event loop, and handles graceful shutdown.

#### `data_ingestion.py`
- Connects to Interactive Brokers via WebSocket
- Subscribes to real-time market data feeds
- Fetches historical data for backtesting
- Persists tick data to database
- Provides fallback to REST polling if WebSocket fails

#### `strategy_engine.py`
- Processes incoming price streams
- Calculates technical indicators (SMA, RSI, etc.)
- Maintains internal position state
- Generates trading signals based on strategy logic
- Example: Moving average crossover strategy

#### `risk_manager.py`
- Validates orders against risk limits
- Enforces maximum position size per instrument
- Monitors leverage constraints
- Tracks daily P&L and loss limits
- Activates circuit breaker when thresholds are breached
- Resets counters daily

#### `execution_engine.py`
- Translates strategy signals into broker orders
- Handles order submission and tracking
- Manages order lifecycle (pending, filled, cancelled)
- Tracks partial fills and errors
- Reconciles internal positions with broker positions
- Provides order status updates

#### `monitoring.py`
- Sends WhatsApp alerts via Twilio
- Monitors system health with scheduled checks
- Alerts on order failures
- Alerts on portfolio drawdown thresholds
- Alerts on circuit breaker activation
- Logs all critical events

#### `database.py`
- Async SQLite operations using aiosqlite
- Stores tick data for audit trail
- Records order history and fills
- Tracks trade execution details
- Maintains daily P&L records
- Creates and manages database schema

#### `config.py`
- Centralized configuration management
- Loads environment variables from .env
- Defines risk parameters (limits, leverage, etc.)
- Broker connection settings
- Alert configuration

---

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        MARKET DATA FEED                          │
│                    (Interactive Brokers)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │ data_ingestion.py│
                   │  - WebSocket     │
                   │  - REST API      │
                   └────┬────────┬────┘
                        │        │
           ┌────────────┘        └──────────────┐
           ▼                                     ▼
    ┌─────────────┐                      ┌────────────┐
    │ database.py │                      │            │
    │  Store ticks│                      │            │
    └─────────────┘                      │            │
                                         ▼            │
                              ┌────────────────────┐  │
                              │ strategy_engine.py │  │
                              │  - Indicators      │  │
                              │  - State tracking  │  │
                              │  - Signal gen      │  │
                              └─────────┬──────────┘  │
                                        │             │
                                        ▼             │
                              ┌────────────────────┐  │
                              │  risk_manager.py   │  │
                              │  - Validate signal │  │
                              │  - Check limits    │  │
                              │  - Circuit breaker │  │
                              └─────────┬──────────┘  │
                                        │             │
                    ┌───────────────────┼─────────────┘
                    │ Valid?            │
                    ▼                   ▼
              ┌──────────┐        ┌────────────────────┐
              │ REJECTED │        │ execution_engine.py│
              │   LOG    │        │  - Place order     │
              └─────┬────┘        │  - Track fills     │
                    │             │  - Handle errors   │
                    │             └─────────┬──────────┘
                    │                       │
                    │                       ▼
                    │             ┌────────────────────┐
                    │             │  BROKER (IB TWS)   │
                    │             │  - Order routing   │
                    │             │  - Execution       │
                    │             └─────────┬──────────┘
                    │                       │
                    │                       ▼
                    │             ┌────────────────────┐
                    │             │   Position Update  │
                    │             │   Fill Notification│
                    │             └─────────┬──────────┘
                    │                       │
                    │                       │ (on fill)
                    │                       ▼
                    │             ┌────────────────────┐
                    │             │ execution_engine.py│
                    │             │  LOG TRADE TO DB   │
                    │             │  - Symbol, qty     │
                    │             │  - Price, PnL      │
                    │             │  - Commission      │
                    │             └─────────┬──────────┘
                    │                       │
                    └───────────┬───────────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │   monitoring.py   │
                      │  - Health checks  │
                      │  - WhatsApp alerts│
                      │  - Log events     │
                      │  - Log fills      │
                      └─────────┬─────────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │ ALERTS & LOGGING  │
                      │  - Twilio         │
                      │  - Loguru         │
                      │  - Database audit │
                      │  - Trades table   │
                      └───────────────────┘
```

---

## Quick Start

### 1. Setup Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

**Important:** Set `IB_PORT=7497` for paper trading (recommended for testing)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python -c "import asyncio; from database import Database; asyncio.run(Database().initialize())"
```

### 4. Start IB Paper Trading
- Open IB TWS or IB Gateway
- Login to your paper trading account
- Enable API connections: Configure → Settings → API → Settings
- Check "Enable ActiveX and Socket Clients"
- Add 127.0.0.1 to trusted IPs

### 5. Run the System
```bash
python main.py
```

### 6. Emergency Stop
To immediately halt trading:
```bash
touch STOP
```
Or press `Ctrl+C` for graceful shutdown.

---

## MVP Critical Features

### ✅ Implemented
- Real-time market data streaming
- Async/await architecture for performance
- Comprehensive risk management
- Order execution with error handling
- Position reconciliation
- WhatsApp alerts for critical events
- SQLite persistence for audit trail
- Circuit breaker for safety
- Daily P&L tracking
- Extensible strategy engine

### 🚧 MVP Requirements (In Progress)
- **Auto-reconnection logic** - Handles IB disconnections automatically
- **Emergency kill switch** - File-based stop mechanism
- **Paper trading mode** - Safe testing without real money

---

## Safety Features

### Paper Trading Mode
Always test with paper trading first:
- Set `IB_PORT=7497` in `.env` (paper trading)
- Live trading uses port `7496` (DO NOT use until fully tested)

### Emergency Stop Mechanisms
1. **File-based kill switch**: `touch STOP` in project directory
2. **Keyboard interrupt**: `Ctrl+C` for graceful shutdown
3. **Circuit breaker**: Automatic halt on loss limits

### Connection Resilience
- Auto-reconnects on IB disconnection
- Exponential backoff on failures
- Alerts sent on connection issues

---

## Configuration

### Risk Parameters (`.env`)
```bash
MAX_POSITION_SIZE=10000      # Max $ per position
MAX_LEVERAGE=2.0             # Maximum leverage
DAILY_LOSS_LIMIT=500         # Stop trading at -$500/day
```

### Testing Checklist
Before live trading:
- ✅ Test with paper account for at least 1 week
- ✅ Verify risk limits work correctly
- ✅ Confirm alerts are received
- ✅ Test emergency stop mechanism
- ✅ Review all logged trades in database
- ✅ Validate position reconciliation

---

## Troubleshooting

### Connection Issues
```
Error: Connection refused to IB
```
**Solution:** 
- Ensure IB TWS/Gateway is running
- Check API is enabled in IB settings
- Verify correct port (7497 for paper, 7496 for live)

### No Market Data
```
Warning: No market data received
```
**Solution:**
- Check market is open
- Verify you have market data subscriptions
- Confirm symbol is valid

### Circuit Breaker Activated
```
CIRCUIT BREAKER ACTIVATED - Trading halted
```
**Solution:**
- Review trades in database
- Check `daily_pnl` table
- Will auto-reset next trading day
- Manual reset: restart system (if confident)
