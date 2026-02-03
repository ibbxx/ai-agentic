"""
Executor - Runs the plan with safety limits (max steps, timeout).
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.agent.tools import task_tool, scheduler_tool, approval_tool, preference_tool, proposal_tool
from core.agent.tools import shell_tool, file_tool, app_tool
from core.agent.guardrails import is_high_risk, get_risk_description
from core.models import ApprovalRequest, ApprovalStatus
from core.db import crud
from core.safety import MAX_STEPS_PER_RUN, TOOL_TIMEOUT_SECONDS
from core.logging_config import get_logger

logger = get_logger(__name__)

TOOL_REGISTRY = {
    "task_tool": task_tool,
    "scheduler_tool": scheduler_tool,
    "approval_tool": approval_tool,
    "preference_tool": preference_tool,
    "proposal_tool": proposal_tool,
    "shell_tool": shell_tool,
    "file_tool": file_tool,
    "app_tool": app_tool,
}

def execute_plan(plan: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """Execute the plan with safety limits."""
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
    
    # Safety: limit max steps
    if len(steps) > MAX_STEPS_PER_RUN:
        logger.warning(f"Plan has {len(steps)} steps, limiting to {MAX_STEPS_PER_RUN}")
        steps = steps[:MAX_STEPS_PER_RUN]
    
    for i, step in enumerate(steps):
        tool_name = step.get("tool")
        action = step.get("action")
        params = step.get("params", {})
        
        logger.info(f"Executing step {i+1}/{len(steps)}: {tool_name}.{action}")
        
        if is_high_risk(tool_name, action):
            risk_desc = get_risk_description(tool_name, action)
            
            # Add command details for shell_tool
            if tool_name == "shell_tool":
                risk_desc += f": `{params.get('command', '')}`"
            elif tool_name == "app_tool":
                risk_desc += f": {params.get('app', '')}"
            elif tool_name == "file_tool":
                risk_desc += f": {params.get('path', '')}"
            
            approval_payload = {
                "tool": tool_name, 
                "action": action, 
                "params": params, 
                "description": risk_desc
            }
            approval_req = crud.create_approval_request(
                db, user_id, 
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
        
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            results.append({"tool": tool_name, "error": f"Tool '{tool_name}' not found"})
            continue
        
        try:
            result = tool.execute(action, params, user_id, db)
            results.append({"tool": tool_name, "action": action, "result": result})
        except Exception as e:
            logger.error(f"Tool error: {e}")
            results.append({"tool": tool_name, "action": action, "error": str(e)})
    
    has_error = any("error" in r for r in results)
    needs_approval = len(pending_approvals) > 0
    
    return {
        "success": not has_error and not needs_approval, 
        "results": results, 
        "pending_approvals": pending_approvals, 
        "needs_approval": needs_approval
    }

def execute_approved_action(approval_id: int, user_id: int, db: Session) -> Dict[str, Any]:
    """Execute a previously approved action."""
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    
    if not req:
        return {"success": False, "error": f"Approval #{approval_id} not found"}
    if req.user_id != user_id:
        return {"success": False, "error": "You can only approve your own requests"}
    if req.status != ApprovalStatus.PENDING:
        return {"success": False, "error": f"Request is already {req.status.value}"}
    
    payload = req.action_payload_json
    tool_name = payload.get("tool")
    action = payload.get("action")
    params = payload.get("params", {})
    
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return {"success": False, "error": f"Tool '{tool_name}' not found"}
    
    try:
        logger.info(f"Executing approved action: {tool_name}.{action}")
        result = tool.execute(action, params, user_id, db)
        crud.update_approval_status(db, approval_id, ApprovalStatus.APPROVED)
        return {"success": True, "result": result, "approval_id": approval_id}
    except Exception as e:
        logger.error(f"Approved action failed: {e}")
        return {"success": False, "error": str(e)}
