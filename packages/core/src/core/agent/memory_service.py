"""
Memory Service - Key-value preferences and reflection storage.
"""
from sqlalchemy.orm import Session
from core.models import Memory
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# Default preferences
DEFAULT_PREFERENCES = {
    "brief_format": "detailed",  # detailed, compact, minimal
    "brief_time": "07:30",
    "timezone": "Asia/Makassar",
    "priority_display": True,
    "due_date_display": True,
}

def get_preference(db: Session, user_id: int, key: str) -> Any:
    """Get a single preference value."""
    prefs = get_all_preferences(db, user_id)
    return prefs.get(key, DEFAULT_PREFERENCES.get(key))

def get_all_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    """Get all user preferences, merged with defaults."""
    mem = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.key == "preferences"
    ).first()
    
    prefs = dict(DEFAULT_PREFERENCES)
    if mem and mem.value_json:
        prefs.update(mem.value_json)
    return prefs

def set_preference(db: Session, user_id: int, key: str, value: Any) -> Dict[str, Any]:
    """Set a single preference value."""
    prefs = get_all_preferences(db, user_id)
    prefs[key] = value
    
    mem = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.key == "preferences"
    ).first()
    
    if mem:
        mem.value_json = prefs
        mem.updated_at = datetime.utcnow()
    else:
        mem = Memory(user_id=user_id, key="preferences", value_json=prefs)
        db.add(mem)
    
    db.commit()
    logger.info(f"[Memory] Set preference {key}={value} for user {user_id}")
    return prefs

def add_reflection(db: Session, user_id: int, run_id: int, reflection: Dict[str, Any]):
    """
    Add a reflection after an agent run.
    Appends to reflection_log memory.
    """
    mem = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.key == "reflection_log"
    ).first()
    
    log = []
    if mem and mem.value_json:
        log = mem.value_json if isinstance(mem.value_json, list) else []
    
    # Keep last 50 reflections
    if len(log) >= 50:
        log = log[-49:]
    
    log.append({
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "what_worked": reflection.get("what_worked"),
        "what_failed": reflection.get("what_failed"),
        "suggestion": reflection.get("suggestion"),
    })
    
    if mem:
        mem.value_json = log
        mem.updated_at = datetime.utcnow()
    else:
        mem = Memory(user_id=user_id, key="reflection_log", value_json=log)
        db.add(mem)
    
    db.commit()
    logger.info(f"[Memory] Added reflection for run {run_id}")

def get_reflections(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent reflections."""
    mem = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.key == "reflection_log"
    ).first()
    
    if not mem or not mem.value_json:
        return []
    
    log = mem.value_json if isinstance(mem.value_json, list) else []
    return log[-limit:]

def format_preferences_display(prefs: Dict[str, Any]) -> str:
    """Format preferences for display."""
    lines = ["⚙️ **Your Preferences**\n"]
    lines.append(f"• Brief Time: {prefs.get('brief_time', '07:30')}")
    lines.append(f"• Brief Format: {prefs.get('brief_format', 'detailed')}")
    lines.append(f"• Timezone: {prefs.get('timezone', 'Asia/Makassar')}")
    lines.append(f"• Show Priority: {'Yes' if prefs.get('priority_display', True) else 'No'}")
    lines.append(f"• Show Due Date: {'Yes' if prefs.get('due_date_display', True) else 'No'}")
    return "\n".join(lines)
