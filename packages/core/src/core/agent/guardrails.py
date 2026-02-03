"""
High-Risk Actions Configuration
"""

# Define high-risk actions that require approval
HIGH_RISK_ACTIONS = {
    # Tool: [list of high-risk action names]
    "task_tool": ["delete", "delete_all", "purge"],
    "file_tool": ["delete", "move", "overwrite"],
    "email_tool": ["send", "send_bulk"],
    "external_tool": ["webhook", "http_request"],
    "db_tool": ["drop", "truncate", "delete_all"],
}

def is_high_risk(tool_name: str, action: str) -> bool:
    """
    Check if a tool+action combination is high-risk.
    """
    high_risk_list = HIGH_RISK_ACTIONS.get(tool_name, [])
    return action.lower() in [a.lower() for a in high_risk_list]

def get_risk_description(tool_name: str, action: str) -> str:
    """
    Get human-readable description of the risk.
    """
    descriptions = {
        ("task_tool", "delete"): "Permanently delete a task",
        ("task_tool", "delete_all"): "Delete all tasks",
        ("file_tool", "delete"): "Delete a file from storage",
        ("email_tool", "send"): "Send an email to external recipient",
        ("external_tool", "webhook"): "Make external HTTP request",
    }
    return descriptions.get((tool_name, action), f"Execute {action} on {tool_name}")
