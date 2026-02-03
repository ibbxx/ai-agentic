"""
Scheduler Tool - Daily brief using Supabase.
"""
from typing import Dict, Any
from core.db import crud

def execute(action: str, params: Dict[str, Any], user_id: int, db) -> Dict[str, Any]:
    """Execute scheduler-related actions."""
    
    if action == "daily_brief":
        tasks = crud.get_tasks_by_user(user_id, "open")
        return {
            "success": True,
            "tasks": [{"id": t["id"], "title": t["title"]} for t in tasks[:10]]
        }
    
    else:
        return {"success": False, "error": f"Unknown action: {action}"}
