"""
Approval Tool - Manage approval requests using Supabase.
"""
from typing import Dict, Any
from core.db import crud
from core.agent.tools import task_tool, shell_tool, file_tool, app_tool, ui_tool, vision_tool

TOOL_REGISTRY = {
    "task_tool": task_tool,
    "shell_tool": shell_tool,
    "file_tool": file_tool,
    "app_tool": app_tool,
    "ui_tool": ui_tool,
    "vision_tool": vision_tool,
}

def execute(action: str, params: Dict[str, Any], user_id: int, db) -> Dict[str, Any]:
    """Execute approval-related actions."""
    
    if action == "approve":
        approval_id = params.get("approval_id")
        if not approval_id:
            return {"success": False, "error": "Approval ID required"}
        
        request = crud.get_approval_request(approval_id)
        if not request:
            return {"success": False, "error": f"Request #{approval_id} not found"}
        
        if request["user_id"] != user_id:
            return {"success": False, "error": "You can only approve your own requests"}
        
        if request["status"] != "pending":
            return {"success": False, "error": f"Request already {request['status']}"}
        
        # Execute the approved action - NO, let the handler execute it!
        # Just return the payload so the handler can run it with full context (photos, updates, etc)
        payload = request["action_payload_json"]
        
        crud.update_approval_status(approval_id, "approved")
        
        return {
            "success": True, 
            "approval_id": approval_id, 
            "approved_payload": payload, # Return this for handler to execute
            "message": "Approved. Executing actions..."
        }
    
    elif action == "list":
        # List pending approvals
        requests = []  # TODO: Implement list
        return {"success": True, "requests": requests}
    
    else:
        return {"success": False, "error": f"Unknown action: {action}"}
