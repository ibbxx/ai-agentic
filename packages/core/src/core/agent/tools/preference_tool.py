"""
Preference Tool - Manages user preferences.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.agent.memory_service import (
    get_all_preferences, 
    set_preference, 
    format_preferences_display
)

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute preference-related actions.
    Actions: get, set
    """
    if action == "get":
        prefs = get_all_preferences(db, user_id)
        display = format_preferences_display(prefs)
        return {"preferences": prefs, "display": display, "success": True}
    
    elif action == "set":
        key = params.get("key")
        value = params.get("value")
        if not key:
            return {"success": False, "error": "Preference key is required"}
        
        prefs = set_preference(db, user_id, key, value)
        return {"preferences": prefs, "key": key, "value": value, "success": True}
    
    else:
        return {"error": f"Unknown preference action: {action}"}
