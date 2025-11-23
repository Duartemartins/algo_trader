"""Basic tests for critical system components."""
import asyncio
import pytest
from datetime import date

from risk_manager import RiskManager
from config import config


def test_risk_manager_position_limit():
    """Test that position size limit is enforced."""
    risk_manager = RiskManager()
    
    # Valid order within limits
    signal = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 50,  # ~$5000 at $100/share
        'type': 'MARKET'
    }
    
    is_valid, reason = risk_manager.validate_order(signal)
    assert is_valid, f"Valid order rejected: {reason}"
    
    # Order exceeding position limit
    signal_large = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 1000,  # ~$100,000 at $100/share
        'type': 'MARKET'
    }
    
    is_valid, reason = risk_manager.validate_order(signal_large)
    assert not is_valid, "Large order should be rejected"
    assert "Position size" in reason


def test_risk_manager_daily_loss_limit():
    """Test that daily loss limit triggers circuit breaker."""
    risk_manager = RiskManager()
    
    # Simulate daily loss
    risk_manager.update_pnl(-config.DAILY_LOSS_LIMIT - 100)
    
    signal = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 10,
        'type': 'MARKET'
    }
    
    is_valid, reason = risk_manager.validate_order(signal)
    assert not is_valid, "Order should be rejected after loss limit"
    assert risk_manager.circuit_breaker_active, "Circuit breaker should be active"


def test_risk_manager_daily_reset():
    """Test that risk counters reset on new day."""
    risk_manager = RiskManager()
    
    # Set a loss and activate circuit breaker
    risk_manager.update_pnl(-config.DAILY_LOSS_LIMIT - 100)
    assert risk_manager.circuit_breaker_active
    
    # Simulate new day
    risk_manager._reset_daily_counters()
    
    assert risk_manager.daily_pnl == 0.0, "Daily P&L should reset"
    assert not risk_manager.circuit_breaker_active, "Circuit breaker should reset"


def test_kill_switch_file():
    """Test that kill switch file can be created and detected."""
    from pathlib import Path
    from main import check_kill_switch, KILL_SWITCH_FILE
    
    # Ensure file doesn't exist
    if KILL_SWITCH_FILE.exists():
        KILL_SWITCH_FILE.unlink()
    
    assert not check_kill_switch(), "Kill switch should not be active"
    
    # Create kill switch
    KILL_SWITCH_FILE.touch()
    assert check_kill_switch(), "Kill switch should be active"
    
    # Cleanup
    KILL_SWITCH_FILE.unlink()
    assert not check_kill_switch(), "Kill switch should be inactive after removal"


async def test_database_initialization():
    """Test that database initializes correctly."""
    from database import Database
    import os
    
    test_db_path = "./test_trading.db"
    
    # Remove test db if exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = Database()
    db.db_path = test_db_path
    
    await db.initialize()
    
    # Check that database file was created
    assert os.path.exists(test_db_path), "Database file should be created"
    
    # Cleanup
    os.remove(test_db_path)


if __name__ == "__main__":
    print("Running basic system tests...")
    
    # Run sync tests
    test_risk_manager_position_limit()
    print("✓ Position limit test passed")
    
    test_risk_manager_daily_loss_limit()
    print("✓ Daily loss limit test passed")
    
    test_risk_manager_daily_reset()
    print("✓ Daily reset test passed")
    
    test_kill_switch_file()
    print("✓ Kill switch test passed")
    
    # Run async test
    asyncio.run(test_database_initialization())
    print("✓ Database initialization test passed")
    
    print("\n✅ All tests passed!")
