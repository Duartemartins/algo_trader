"""Monitoring and alerting system."""
from typing import Dict
from loguru import logger
from twilio.rest import Client
import schedule
import time
from threading import Thread

from config import config


class Monitor:
    """Handles system monitoring and alerts."""
    
    def __init__(self):
        self.twilio_client = None
        self._setup_twilio()
        self.alerts_sent = []
        self.is_running = False
        logger.info("Monitor initialized")
    
    def _setup_twilio(self):
        """Initialize Twilio client for WhatsApp alerts."""
        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = Client(
                    config.TWILIO_ACCOUNT_SID,
                    config.TWILIO_AUTH_TOKEN
                )
                logger.info("Twilio client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
        else:
            logger.warning("Twilio credentials not configured")
    
    def send_whatsapp_alert(self, message: str):
        """Send WhatsApp alert via Twilio."""
        if not self.twilio_client:
            logger.warning("Twilio not configured, skipping alert")
            return
        
        try:
            msg = self.twilio_client.messages.create(
                body=message,
                from_=config.TWILIO_WHATSAPP_FROM,
                to=config.TWILIO_WHATSAPP_TO
            )
            logger.info(f"WhatsApp alert sent: {msg.sid}")
            self.alerts_sent.append({
                'message': message,
                'time': time.time(),
                'sid': msg.sid
            })
        except Exception as e:
            logger.error(f"Failed to send WhatsApp alert: {e}")
    
    def alert_order_failed(self, order_id: str, reason: str):
        """Alert when an order fails."""
        message = f"🚨 Order Failed\nOrder ID: {order_id}\nReason: {reason}"
        self.send_whatsapp_alert(message)
        logger.warning(f"Order failed alert sent: {order_id}")
    
    def alert_drawdown(self, current_pnl: float, threshold: float):
        """Alert when drawdown exceeds threshold."""
        message = f"⚠️ Drawdown Alert\nCurrent P&L: ${current_pnl:.2f}\nThreshold: ${threshold:.2f}"
        self.send_whatsapp_alert(message)
        logger.warning(f"Drawdown alert sent: ${current_pnl:.2f}")
    
    def alert_circuit_breaker(self, reason: str):
        """Alert when circuit breaker is triggered."""
        message = f"🛑 Circuit Breaker Activated\nReason: {reason}\nTrading halted"
        self.send_whatsapp_alert(message)
        logger.critical("Circuit breaker alert sent")
    
    def alert_system_error(self, error: str):
        """Alert on system errors."""
        message = f"❌ System Error\n{error}"
        self.send_whatsapp_alert(message)
        logger.error(f"System error alert sent: {error}")
    
    def check_system_health(self):
        """Periodic health check."""
        logger.info("System health check completed")
        # Add actual health checks here
    
    def start(self):
        """Start monitoring scheduler."""
        schedule.every(5).minutes.do(self.check_system_health)
        
        def run_scheduler():
            self.is_running = True
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        thread = Thread(target=run_scheduler, daemon=True)
        thread.start()
        logger.info("Monitoring scheduler started")
    
    def stop(self):
        """Stop monitoring scheduler."""
        self.is_running = False
        logger.info("Monitoring scheduler stopped")
