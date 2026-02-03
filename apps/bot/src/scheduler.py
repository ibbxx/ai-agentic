"""
Scheduler Service - Daily briefs using Supabase.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
from core.config import get_settings
from core.supabase_client import get_supabase
import logging
import pytz
from datetime import datetime

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()

async def send_daily_brief(app: Application):
    """Send daily brief to all users."""
    try:
        supabase = get_supabase()
        
        # Get all users
        result = supabase.table("users").select("*").execute()
        users = result.data
        
        for user in users:
            user_id = user["id"]
            telegram_id = user.get("telegram_user_id")
            user_tz = user.get("timezone", "Asia/Makassar")
            
            if not telegram_id:
                continue
            
            # Check if it's morning in user's timezone
            try:
                tz = pytz.timezone(user_tz)
                now = datetime.now(tz)
                if now.hour != 7 or now.minute > 35:
                    continue
            except:
                pass
            
            # Get open tasks
            tasks_result = supabase.table("tasks").select("id,title").eq("user_id", user_id).eq("status", "open").execute()
            tasks = tasks_result.data
            
            if not tasks:
                message = "☀️ Good morning! You have no open tasks."
            else:
                task_list = "\n".join([f"  - {t['title']}" for t in tasks[:5]])
                message = f"☀️ Daily Brief:\n\nOpen Tasks ({len(tasks)}):\n{task_list}"
            
            try:
                await app.bot.send_message(chat_id=int(telegram_id), text=message)
                logger.info(f"Sent daily brief to {telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send brief to {telegram_id}: {e}")
                
    except Exception as e:
        logger.error(f"Daily brief error: {e}")

def setup_scheduler(app: Application):
    """Setup the scheduler with daily brief job."""
    scheduler.add_job(
        send_daily_brief,
        CronTrigger(minute=30),
        args=[app],
        id="send_daily_brief",
        replace_existing=True
    )
    scheduler.start()
    logger.info("[Scheduler] Started with daily brief at XX:30 (checking user timezones)")

def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Scheduler] Shutdown complete")
