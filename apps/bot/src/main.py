#!/usr/bin/env python3
import sys
import os

# Add the bot src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add project root for core package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from telegram.ext import Application
from core.config import get_settings
from handlers import setup_handlers
from scheduler import setup_scheduler, shutdown_scheduler
import logging
import signal

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

settings = get_settings()

def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    logger.info("Starting Bot...")
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Setup handlers
    setup_handlers(app)
    
    # Setup scheduler
    setup_scheduler(app)
    
    # Graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        shutdown_scheduler()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start polling
    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
