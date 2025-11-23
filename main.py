"""Main entry point for the algorithmic trading system."""
import asyncio
import os
from pathlib import Path
from loguru import logger
from rich.console import Console

from config import config
from data_ingestion import DataIngestion
from strategy_engine import StrategyEngine
from risk_manager import RiskManager
from execution_engine import ExecutionEngine
from monitoring import Monitor

console = Console()
KILL_SWITCH_FILE = Path("STOP")


def check_kill_switch() -> bool:
    """Check if emergency kill switch is activated."""
    if KILL_SWITCH_FILE.exists():
        return True
    return False


async def main():
    """Initialize and run the trading system."""
    # Setup logging
    os.makedirs(config.LOG_PATH, exist_ok=True)
    logger.add(
        f"{config.LOG_PATH}/trading_{{time}}.log",
        rotation="1 day",
        retention="30 days",
        level=config.LOG_LEVEL
    )
    
    console.print("[bold green]Starting Algorithmic Trading System[/bold green]")
    
    # Check paper trading mode
    if config.IB_PORT == 7497:
        console.print("[bold yellow]⚠️  Running in PAPER TRADING mode[/bold yellow]")
    else:
        console.print("[bold red]🔴 Running in LIVE TRADING mode[/bold red]")
        console.print("[yellow]Press Ctrl+C within 5 seconds to abort...[/yellow]")
        await asyncio.sleep(5)
    
    logger.info("Initializing trading system components")
    
    try:
        # Initialize components
        data_ingestion = DataIngestion()
        strategy_engine = StrategyEngine()
        risk_manager = RiskManager()
        execution_engine = ExecutionEngine()
        monitor = Monitor()
        
        # Connect to broker
        await data_ingestion.connect()
        logger.info("Connected to Interactive Brokers")
        
        # Start monitoring
        monitor.start()
        
        # Main trading loop
        console.print("[bold cyan]Trading system is running...[/bold cyan]")
        console.print("[dim]Emergency stop: touch STOP or press Ctrl+C[/dim]")
        
        while True:
            # Check kill switch
            if check_kill_switch():
                console.print("[bold red]🛑 KILL SWITCH ACTIVATED - Stopping system[/bold red]")
                logger.critical("Emergency kill switch activated")
                monitor.alert_system_error("Emergency kill switch activated")
                break
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        console.print("[bold yellow]\nShutting down gracefully...[/bold yellow]")
        logger.info("Received shutdown signal (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        console.print(f"[bold red]Error: {e}[/bold red]")
        monitor.alert_system_error(f"Fatal error: {e}")
    finally:
        # Cleanup
        console.print("[dim]Cleaning up resources...[/dim]")
        await data_ingestion.disconnect()
        monitor.stop()
        
        # Remove kill switch file if it exists
        if KILL_SWITCH_FILE.exists():
            KILL_SWITCH_FILE.unlink()
            logger.info("Removed kill switch file")
        
        logger.info("Trading system stopped")
        console.print("[bold green]✓ System stopped safely[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
