"""
Planner - Creates execution plan based on intent.
"""
from core.parser import Intent, ParsedIntent
from typing import Dict, Any

def make_plan(parsed: ParsedIntent) -> Dict[str, Any]:
    """Generate an execution plan based on classified intent."""
    intent = parsed.intent
    params = parsed.params
    
    # Task intents
    if intent == Intent.ADD_TASK:
        return {"steps": [{"tool": "task_tool", "action": "create", "params": {"title": params.get("title", "")}}]}
    
    elif intent == Intent.LIST_TASKS:
        return {"steps": [{"tool": "task_tool", "action": "list", "params": {}}]}
    
    elif intent == Intent.DONE_TASK:
        return {"steps": [{"tool": "task_tool", "action": "close", "params": {"task_id": params.get("task_id")}}]}
    
    elif intent == Intent.DELETE_TASK:
        return {"steps": [{"tool": "task_tool", "action": "delete", "params": {"task_id": params.get("task_id")}}]}
    
    elif intent == Intent.DAILY_BRIEF:
        return {"steps": [{"tool": "scheduler_tool", "action": "daily_brief", "params": {}}]}
    
    elif intent == Intent.APPROVE:
        return {"steps": [{"tool": "approval_tool", "action": "approve", "params": {"approval_id": params.get("approval_id")}}]}
    
    # Preference intents
    elif intent == Intent.MY_PREFS:
        return {"steps": [{"tool": "preference_tool", "action": "get", "params": {}}]}
    
    elif intent == Intent.SET_PREF:
        return {"steps": [{"tool": "preference_tool", "action": "set", "params": {"key": params.get("key"), "value": params.get("value")}}]}
    
    # Proposal intents
    elif intent == Intent.LIST_PROPOSALS:
        return {"steps": [{"tool": "proposal_tool", "action": "list", "params": {}}]}
    
    elif intent == Intent.APPROVE_PROPOSAL:
        return {"steps": [{"tool": "proposal_tool", "action": "approve", "params": {"proposal_id": params.get("proposal_id")}}]}
    
    elif intent == Intent.REJECT_PROPOSAL:
        return {"steps": [{"tool": "proposal_tool", "action": "reject", "params": {"proposal_id": params.get("proposal_id")}}]}
    
    elif intent == Intent.ROLLBACK_PROPOSAL:
        return {"steps": [{"tool": "proposal_tool", "action": "rollback", "params": {"proposal_id": params.get("proposal_id")}}]}
    
    # Computer use intents
    elif intent == Intent.RUN_COMMAND:
        return {"steps": [{"tool": "shell_tool", "action": "run", "params": {"command": params.get("command")}}]}
    
    elif intent == Intent.READ_FILE:
        return {"steps": [{"tool": "file_tool", "action": "read", "params": {"path": params.get("path")}}]}
    
    elif intent == Intent.WRITE_FILE:
        return {"steps": [{"tool": "file_tool", "action": "write", "params": {"path": params.get("path"), "content": params.get("content", "")}}]}
    
    elif intent == Intent.LIST_FILES:
        return {"steps": [{"tool": "file_tool", "action": "list", "params": {"path": params.get("path", ".")}}]}
    
    elif intent == Intent.OPEN_APP:
        step_params = {"app": params.get("app")}
        if params.get("file"):
            step_params["file"] = params.get("file")
        if params.get("url"):
            step_params["url"] = params.get("url")
        return {"steps": [{"tool": "app_tool", "action": "open", "params": step_params}]}
    
    elif intent == Intent.CLOSE_APP:
        return {"steps": [{"tool": "app_tool", "action": "close", "params": {"app": params.get("app")}}]}
    
    elif intent == Intent.SCREENSHOT:
        return {"steps": [{"tool": "app_tool", "action": "screenshot", "params": {}}]}
    
    else:
        return {"steps": [], "fallback": "unknown_intent", "original_text": params.get("text", "")}
