"""
CRUD Operations - Using Supabase REST API.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from core.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)

# ========== USERS ==========
def get_or_create_user(telegram_user_id: str, name: str = None) -> Dict[str, Any]:
    """Get existing user or create new one."""
    supabase = get_supabase()
    
    # Try to find existing user
    result = supabase.table("users").select("*").eq("telegram_user_id", telegram_user_id).execute()
    
    if result.data:
        return result.data[0]
    
    # Create new user
    new_user = {
        "telegram_user_id": telegram_user_id,
        "name": name or f"User_{telegram_user_id[-4:]}",
        "timezone": "Asia/Makassar",
    }
    result = supabase.table("users").insert(new_user).execute()
    logger.info(f"Created new user: {telegram_user_id}")
    return result.data[0]

def get_user_by_telegram_id(telegram_user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by Telegram ID."""
    supabase = get_supabase()
    result = supabase.table("users").select("*").eq("telegram_user_id", telegram_user_id).execute()
    return result.data[0] if result.data else None

# ========== TASKS ==========
def create_task(user_id: int, title: str, description: str = None) -> Dict[str, Any]:
    """Create a new task."""
    supabase = get_supabase()
    new_task = {
        "user_id": user_id,
        "title": title,
        "description": description or "",
        "status": "open",
    }
    result = supabase.table("tasks").insert(new_task).execute()
    return result.data[0]

def get_tasks_by_user(user_id: int, status: str = None) -> List[Dict[str, Any]]:
    """Get tasks for a user, optionally filtered by status."""
    supabase = get_supabase()
    query = supabase.table("tasks").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return result.data

def close_task(task_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Mark task as done."""
    supabase = get_supabase()
    result = supabase.table("tasks").update({"status": "done"}).eq("id", task_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None

def delete_task(task_id: int, user_id: int) -> bool:
    """Delete a task."""
    supabase = get_supabase()
    result = supabase.table("tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()
    return len(result.data) > 0

# ========== MESSAGES ==========
def log_message(user_id: int, text: str, source: str = "telegram") -> Dict[str, Any]:
    """Log a message."""
    supabase = get_supabase()
    new_message = {
        "user_id": user_id,
        "text": text[:4000],  # Limit length
        "source": source,
    }
    result = supabase.table("messages").insert(new_message).execute()
    return result.data[0] if result.data else {}

# ========== APPROVAL REQUESTS ==========
def create_approval_request(user_id: int, action_type: str, payload: Dict) -> Dict[str, Any]:
    """Create a pending approval request."""
    supabase = get_supabase()
    new_request = {
        "user_id": user_id,
        "action_type": action_type,
        "action_payload_json": payload,
        "status": "pending",
    }
    result = supabase.table("approval_requests").insert(new_request).execute()
    return result.data[0]

def get_approval_request(approval_id: int) -> Optional[Dict[str, Any]]:
    """Get approval request by ID."""
    supabase = get_supabase()
    result = supabase.table("approval_requests").select("*").eq("id", approval_id).execute()
    return result.data[0] if result.data else None

def update_approval_status(approval_id: int, status: str) -> bool:
    """Update approval request status."""
    supabase = get_supabase()
    result = supabase.table("approval_requests").update({"status": status}).eq("id", approval_id).execute()
    return len(result.data) > 0

# ========== MEMORY ==========
def get_user_preferences(user_id: int) -> Dict[str, Any]:
    """Get user preferences from memory."""
    supabase = get_supabase()
    result = supabase.table("memory").select("*").eq("user_id", user_id).eq("memory_type", "preference").execute()
    
    prefs = {}
    for row in result.data:
        prefs[row.get("key", "")] = row.get("value", "")
    return prefs

def set_user_preference(user_id: int, key: str, value: str) -> bool:
    """Set a user preference."""
    supabase = get_supabase()
    
    # Check if exists
    existing = supabase.table("memory").select("id").eq("user_id", user_id).eq("key", key).execute()
    
    if existing.data:
        supabase.table("memory").update({"value": value}).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("memory").insert({
            "user_id": user_id,
            "memory_type": "preference",
            "key": key,
            "value": value,
        }).execute()
    return True

# ========== PROPOSALS ==========
def create_proposal(user_id: int, proposal: Dict) -> Dict[str, Any]:
    """Create an improvement proposal."""
    supabase = get_supabase()
    new_proposal = {
        "user_id": user_id,
        "proposal_json": proposal,
        "status": "pending",
    }
    result = supabase.table("improvement_proposals").insert(new_proposal).execute()
    return result.data[0]

def get_proposals_by_user(user_id: int, status: str = None) -> List[Dict[str, Any]]:
    """Get proposals for a user."""
    supabase = get_supabase()
    query = supabase.table("improvement_proposals").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return result.data

def update_proposal_status(proposal_id: int, status: str) -> bool:
    """Update proposal status."""
    supabase = get_supabase()
    result = supabase.table("improvement_proposals").update({"status": status}).eq("id", proposal_id).execute()
    return len(result.data) > 0
