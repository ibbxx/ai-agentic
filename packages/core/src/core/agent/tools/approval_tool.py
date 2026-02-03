"""
Approval Tool - Manages approval requests with ownership check.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.models import ApprovalRequest, ApprovalStatus
from core.db import crud
from core.agent.executor import execute_approved_action

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute approval-related actions.
    Actions: approve (executes pending high-risk action)
    """
    if action == "approve":
        approval_id = params.get("approval_id")
        if not approval_id:
            return {"success": False, "error": "Approval ID is required"}
        
        # Use the executor's approve function which checks ownership
        return execute_approved_action(approval_id, user_id, db)
    
    elif action == "reject":
        approval_id = params.get("approval_id")
        if not approval_id:
            return {"success": False, "error": "Approval ID is required"}
        
        req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
        if not req:
            return {"success": False, "error": f"Request #{approval_id} not found"}
        
        if req.user_id != user_id:
            return {"success": False, "error": "You can only reject your own requests"}
        
        if req.status != ApprovalStatus.PENDING:
            return {"success": False, "error": f"Request is already {req.status.value}"}
        
        crud.update_approval_status(db, approval_id, ApprovalStatus.REJECTED)
        return {"approval_id": approval_id, "success": True, "status": "rejected"}
    
    else:
        return {"error": f"Unknown approval action: {action}"}
