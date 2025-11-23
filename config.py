"""Configuration management for the trading system."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Interactive Brokers
    IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
    IB_PORT = int(os.getenv("IB_PORT", "7497"))  # 7497=paper, 7496=live
    IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))
    
    # Connection settings
    MAX_RECONNECT_ATTEMPTS = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "5"))
    RECONNECT_DELAY = int(os.getenv("RECONNECT_DELAY", "5"))  # seconds
    
    # Risk Management
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "10000"))
    MAX_LEVERAGE = float(os.getenv("MAX_LEVERAGE", "2.0"))
    DAILY_LOSS_LIMIT = float(os.getenv("DAILY_LOSS_LIMIT", "500"))
    
    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
    TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "./data/trading.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_PATH = os.getenv("LOG_PATH", "./logs")


config = Config()
