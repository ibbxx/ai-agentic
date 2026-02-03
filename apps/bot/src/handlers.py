from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application
from sqlalchemy.orm import Session
from core.database import get_db, SessionLocal
from core.db import crud
from core.config import get_settings
import httpx
import logging
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

settings = get_settings()

API_URL = "http://api:8000" # Docker service name

def get_session():
    return SessionLocal()

async def get_current_user_db(update: Update, db: Session):
    user = update.effective_user
    db_user = crud.get_or_create_user(db, str(user.id), user.full_name)
    return db_user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start menyimpan user ke DB."""
    db = get_session()
    try:
        await get_current_user_db(update, db)
        await update.message.reply_text("Hello! I am your AI Agent. I'm connected and ready.")
        logger.info(f"User {update.effective_user.id} started the bot.")
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text("System error during registration.")
    finally:
        db.close()

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler semua message text -> POST ke API /v1/message."""
    user = update.effective_user
    text = update.message.text
    
    if not text:
        return

    # Ensure user exists in DB locally first (redundant safety)
    db = get_session()
    try:
        await get_current_user_db(update, db)
    except Exception as e:
        logger.error(f"DB Error in message handler: {e}")
    finally:
        db.close()

    # Call API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "telegram_user_id": str(user.id),
                "text": text,
                "message_id": update.message.message_id,
                "chat_id": update.message.chat_id
            }
            logger.info(f"Forwarding message from {user.id} to API: {text}")
            
            response = await client.post(f"{API_URL}/v1/message", json=payload)
            response.raise_for_status()
            
            data = response.json()
            reply_text = data.get("response", "No response from Agent.")
            
            await update.message.reply_text(reply_text)
            
    except httpx.RequestError as e:
        logger.error(f"API Request Error: {e}")
        await update.message.reply_text("⚠️ Could not connect to Brain API.")
    except httpx.HTTPStatusError as e:
        logger.error(f"API Status Error: {e.response.status_code} - {e.response.text}")
        await update.message.reply_text("⚠️ Brain API returned an error.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("An unexpected error occurred.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Just send me a message and I will process it!")

def setup_handlers(app: Application):
    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Message Handler (Filters text & not command)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
