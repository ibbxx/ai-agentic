"""
Task Tool - CRUD operations for tasks using Supabase.
"""
from typing import Dict, Any
from core.db import crud

def execute(action: str, params: Dict[str, Any], user_id: int, db) -> Dict[str, Any]:
    """Execute task-related actions."""
    
    if action == "create":
        title = params.get("title", "").strip()
        if not title:
            return {"success": False, "error": "Title required"}
        
        task = crud.create_task(user_id, title)
        return {"success": True, "task_id": task["id"], "title": task["title"]}
    
    elif action == "list":
        status = params.get("status", "open")
        tasks = crud.get_tasks_by_user(user_id, status)
        return {
            "success": True,
            "tasks": [{"id": t["id"], "title": t["title"], "status": t["status"]} for t in tasks]
        }
    
    elif action == "close":
        task_id = params.get("task_id")
        if not task_id:
            return {"success": False, "error": "Task ID required"}
        
        task = crud.close_task(task_id, user_id)
        if task:
            return {"success": True, "task_id": task_id}
        return {"success": False, "error": "Task not found"}
    
    elif action == "delete":
        task_id = params.get("task_id")
        if not task_id:
            return {"success": False, "error": "Task ID required"}
        
        deleted = crud.delete_task(task_id, user_id)
        if deleted:
            return {"success": True, "task_id": task_id}
        return {"success": False, "error": "Task not found"}
    
    else:
        return {"success": False, "error": f"Unknown action: {action}"}
