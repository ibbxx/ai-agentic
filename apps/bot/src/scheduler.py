"""
Scheduler Service - APScheduler for daily brief and scheduled tasks.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.models import User, Task, TaskStatus
from core.config import get_settings
from datetime import datetime, date
import pytz
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()

async def send_daily_brief(app: Application):
    """
    Generate and send daily brief to all users.
    Runs at 07:30 in each user's timezone (default: Asia/Makassar).
    """
    logger.info("[Scheduler] Running daily brief job...")
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        for user in users:
            try:
                await send_user_brief(app, db, user)
            except Exception as e:
                logger.error(f"[Scheduler] Failed to send brief to user {user.id}: {e}")
    finally:
        db.close()

async def send_user_brief(app: Application, db: Session, user: User):
    """
    Send personalized daily brief to a user.
    """
    # Get user's timezone
    user_tz = user.timezone or settings.TIMEZONE
    
    # Check if it's 07:30 in user's timezone
    tz = pytz.timezone(user_tz)
    now_user = datetime.now(tz)
    
    # Only send if time is around 07:30 (within 5 min window for batching)
    if not (7 <= now_user.hour <= 7 and 25 <= now_user.minute <= 35):
        # Skip if not the right time for this user
        return
    
    # Get open tasks for user
    tasks = db.query(Task).filter(
        Task.user_id == user.id,
        Task.status == TaskStatus.OPEN
    ).order_by(Task.priority.desc(), Task.due_date.asc()).all()
    
    if not tasks:
        brief = "☀️ Good morning! You have no open tasks. Enjoy your day!"
    else:
        # Format brief
        today = date.today()
        
        # Due today
        due_today = [t for t in tasks if t.due_date and t.due_date.date() == today]
        
        # Top 3 by priority
        top_priority = sorted(tasks, key=lambda t: t.priority or 0, reverse=True)[:3]
        
        lines = ["☀️ **Daily Brief**\n"]
        
        # Due today section
        if due_today:
            lines.append(f"📅 **Due Today ({len(due_today)})**")
            for t in due_today:
                lines.append(f"  • {t.title}")
            lines.append("")
        
        # Top priority section
        lines.append("⭐ **Top Priority**")
        for t in top_priority:
            priority_str = f"P{t.priority}" if t.priority else ""
            due_str = f" (due: {t.due_date.strftime('%m/%d')})" if t.due_date else ""
            lines.append(f"  • {t.title} {priority_str}{due_str}")
        lines.append("")
        
        # Summary
        lines.append(f"📋 Total open tasks: {len(tasks)}")
        
        brief = "\n".join(lines)
    
    # Send to user
    try:
        telegram_chat_id = user.telegram_user_id
        await app.bot.send_message(chat_id=telegram_chat_id, text=brief)
        logger.info(f"[Scheduler] Sent daily brief to user {user.id}")
    except Exception as e:
        logger.error(f"[Scheduler] Failed to send message to {user.telegram_user_id}: {e}")

def setup_scheduler(app: Application):
    """
    Setup APScheduler with daily brief job.
    Runs every hour and checks each user's timezone.
    """
    # Run every hour to catch different timezones
    trigger = CronTrigger(
        minute=30,
        timezone=pytz.timezone(settings.TIMEZONE)
    )
    
    scheduler.add_job(
        send_daily_brief,
        trigger=trigger,
        args=[app],
        id="daily_brief",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"[Scheduler] Started with daily brief at XX:30 (checking user timezones)")

def shutdown_scheduler():
    """Gracefully shutdown scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Scheduler] Shutdown complete")
