from telegram.ext import Application
from core.config import get_settings
from src.handlers import setup_handlers
from src.scheduler import setup_scheduler
import asyncio
import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    logger.info("Starting Bot...")
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    setup_handlers(app)
    setup_scheduler(app)
    
    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main()
