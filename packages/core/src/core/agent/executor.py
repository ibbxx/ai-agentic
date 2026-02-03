"""
Executor - Runs the plan by invoking tools with approval gate.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.agent.tools import task_tool, scheduler_tool, approval_tool
from core.agent.guardrails import is_high_risk, get_risk_description
from core.models import ApprovalRequest, ApprovalStatus
from core.db import crud
import json

TOOL_REGISTRY = {
    "task_tool": task_tool,
    "scheduler_tool": scheduler_tool,
    "approval_tool": approval_tool,
}

def execute_plan(plan: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute the plan by invoking registered tools.
    High-risk actions are halted and require approval.
    Returns result_json with outputs from each step.
    """
    results = []
    pending_approvals = []
    
    steps = plan.get("steps", [])
    
    if not steps:
        return {
            "success": False,
            "error": "no_steps",
            "fallback": plan.get("fallback"),
            "original_text": plan.get("original_text")
        }
    
    for step in steps:
        tool_name = step.get("tool")
        action = step.get("action")
        params = step.get("params", {})
        
        # Check if high-risk
        if is_high_risk(tool_name, action):
            # Create approval request instead of executing
            risk_desc = get_risk_description(tool_name, action)
            approval_payload = {
                "tool": tool_name,
                "action": action,
                "params": params,
                "description": risk_desc
            }
            
            approval_req = crud.create_approval_request(
                db, 
                user_id, 
                action_type=f"{tool_name}.{action}",
                payload=approval_payload
            )
            
            pending_approvals.append({
                "approval_id": approval_req.id,
                "action": action,
                "tool": tool_name,
                "description": risk_desc
            })
            continue
        
        # Execute non-high-risk action
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            results.append({"tool": tool_name, "error": f"Tool '{tool_name}' not found"})
            continue
        
        try:
            result = tool.execute(action, params, user_id, db)
            results.append({"tool": tool_name, "action": action, "result": result})
        except Exception as e:
            results.append({"tool": tool_name, "action": action, "error": str(e)})
    
    # Determine overall status
    has_error = any("error" in r for r in results)
    needs_approval = len(pending_approvals) > 0
    
    return {
        "success": not has_error and not needs_approval,
        "results": results,
        "pending_approvals": pending_approvals,
        "needs_approval": needs_approval
    }

def execute_approved_action(approval_id: int, user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute a previously approved action.
    Only the owning user can execute.
    """
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    
    if not req:
        return {"success": False, "error": f"Approval #{approval_id} not found"}
    
    if req.user_id != user_id:
        return {"success": False, "error": "You can only approve your own requests"}
    
    if req.status != ApprovalStatus.PENDING:
        return {"success": False, "error": f"Request is already {req.status.value}"}
    
    # Extract action details
    payload = req.action_payload_json
    tool_name = payload.get("tool")
    action = payload.get("action")
    params = payload.get("params", {})
    
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return {"success": False, "error": f"Tool '{tool_name}' not found"}
    
    try:
        result = tool.execute(action, params, user_id, db)
        
        # Mark as approved
        crud.update_approval_status(db, approval_id, ApprovalStatus.APPROVED)
        
        return {"success": True, "result": result, "approval_id": approval_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
