"""
Planner - Creates execution plan based on intent.
"""
from core.parser import Intent, ParsedIntent
from typing import Dict, Any

def make_plan(parsed: ParsedIntent) -> Dict[str, Any]:
    """
    Generate an execution plan based on classified intent.
    Returns a plan_json structure describing what tools to call.
    """
    intent = parsed.intent
    params = parsed.params
    
    if intent == Intent.ADD_TASK:
        return {
            "steps": [
                {"tool": "task_tool", "action": "create", "params": {"title": params.get("title", "")}}
            ]
        }
    
    elif intent == Intent.LIST_TASKS:
        return {
            "steps": [
                {"tool": "task_tool", "action": "list", "params": {}}
            ]
        }
    
    elif intent == Intent.DONE_TASK:
        return {
            "steps": [
                {"tool": "task_tool", "action": "close", "params": {"task_id": params.get("task_id")}}
            ]
        }
    
    elif intent == Intent.DELETE_TASK:
        # High-risk action - will be halted by executor
        return {
            "steps": [
                {"tool": "task_tool", "action": "delete", "params": {"task_id": params.get("task_id")}}
            ]
        }
    
    elif intent == Intent.DAILY_BRIEF:
        return {
            "steps": [
                {"tool": "scheduler_tool", "action": "daily_brief", "params": {}}
            ]
        }
    
    elif intent == Intent.APPROVE:
        return {
            "steps": [
                {"tool": "approval_tool", "action": "approve", "params": {"approval_id": params.get("approval_id")}}
            ]
        }
    
    else:
        return {
            "steps": [],
            "fallback": "unknown_intent",
            "original_text": params.get("text", "")
        }
