"""
Task Tool - CRUD operations for tasks including high-risk delete.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.db import crud
from core.models import Task

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute task-related actions.
    Actions: create, list, close, delete (high-risk)
    """
    if action == "create":
        title = params.get("title", "")
        if not title:
            return {"error": "Title is required"}
        task = crud.create_task(db, user_id, title)
        return {"task_id": task.id, "title": task.title, "success": True}
    
    elif action == "list":
        tasks = crud.list_open_tasks(db, user_id)
        return {
            "tasks": [{"id": t.id, "title": t.title, "priority": t.priority} for t in tasks],
            "count": len(tasks),
            "success": True
        }
    
    elif action == "close":
        task_id = params.get("task_id")
        if not task_id:
            return {"error": "Task ID is required"}
        task = crud.close_task(db, task_id)
        if task:
            return {"task_id": task_id, "success": True}
        else:
            return {"task_id": task_id, "success": False, "error": "Task not found"}
    
    elif action == "delete":
        # High-risk: Permanent deletion
        task_id = params.get("task_id")
        if not task_id:
            return {"error": "Task ID is required"}
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if task:
            db.delete(task)
            db.commit()
            return {"task_id": task_id, "success": True, "deleted": True}
        else:
            return {"task_id": task_id, "success": False, "error": "Task not found"}
    
    else:
        return {"error": f"Unknown action: {action}"}
