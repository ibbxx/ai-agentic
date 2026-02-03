"""
Verifier - Validates execution results.
"""
from typing import Dict, Any
from core.parser import Intent, ParsedIntent

def verify_result(parsed: ParsedIntent, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that execution results match expected outcomes.
    Returns {ok: bool, issues: list}
    """
    issues = []
    
    if not result.get("success"):
        if result.get("error") == "no_steps":
            issues.append("Unknown command")
        else:
            issues.append("Execution failed")
    
    # Check for tool-level errors
    for r in result.get("results", []):
        if "error" in r:
            issues.append(f"Tool {r.get('tool')}: {r.get('error')}")
    
    # Intent-specific validations
    if parsed.intent == Intent.ADD_TASK:
        results = result.get("results", [])
        if results and results[0].get("result", {}).get("task_id") is None:
            issues.append("Task creation did not return ID")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues
    }
