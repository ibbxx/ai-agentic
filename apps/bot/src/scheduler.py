from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
from core.config import get_settings
from core.database import get_db, SessionLocal
from core.models import Task, TaskStatus

settings = get_settings()

async def daily_brief(application: Application):
    """Sends a daily brief of open tasks."""
    # Note: In a real multi-user scenario, we'd loop through all users with open tasks.
    # For now, we will send to the admin/configured chat_id if pertinent, OR better yet:
    # Iterate users who have open tasks.
    
    db = SessionLocal()
    try:
        # Simple implementation: Loop through all users with open tasks (this might be slow for millions of users, 
        # but fine for private agent bot).
        # Assuming we just want to notify the configured CHAT_ID for now as this is a personal agent.
        
        chat_id = settings.TELEGRAM_CHAT_ID
        if not chat_id:
            return

        # For the configured chat_id specific user (we don't know the DB ID of the admin unless we query by settings)
        # We will just query all open tasks for now and send a dump, assuming single-user agent usage mostly.
        
        open_tasks = db.query(Task).filter(Task.status == TaskStatus.OPEN).all()
        
        if not open_tasks:
            message = "Good morning! ☀️\nYou have no open tasks."
        else:
            task_list = "\n".join([f"- {t.id}: {t.title}" for t in open_tasks])
            message = f"Good morning! ☀️\n\nHere are all open tasks:\n{task_list}"
        
        await application.bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"Error in daily brief: {e}")
    finally:
        db.close()

def setup_scheduler(application: Application):
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    
    # Run at 07:30 daily
    scheduler.add_job(
        daily_brief,
        CronTrigger(hour=7, minute=30),
        args=[application]
    )
    
    scheduler.start()
