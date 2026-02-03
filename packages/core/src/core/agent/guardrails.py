"""
Guardrails - Define high-risk actions that require approval.
"""

# High-risk actions that require user approval before execution
HIGH_RISK_ACTIONS = {
    "task_tool": ["delete", "delete_all", "purge"],
    "file_tool": ["delete", "move", "overwrite", "write"],
    "email_tool": ["send", "send_bulk"],
    "external_tool": ["webhook", "http_request"],
    "shell_tool": ["run"],  # ALL shell commands are high-risk
    "app_tool": ["open", "close", "focus"],  # App control needs approval
    "ui_tool": ["click", "type", "hotkey", "search", "press"],  # UI automation needs approval
}

# Risk descriptions for user display
RISK_DESCRIPTIONS = {
    "task_tool.delete": "Permanently delete a task",
    "task_tool.delete_all": "Delete all tasks",
    "task_tool.purge": "Purge completed tasks",
    "file_tool.delete": "Delete a file or directory",
    "file_tool.move": "Move a file or directory",
    "file_tool.overwrite": "Overwrite an existing file",
    "file_tool.write": "Write to a file",
    "shell_tool.run": "Execute a terminal command",
    "app_tool.open": "Open an application",
    "app_tool.close": "Close an application",
    "app_tool.focus": "Focus an application window",
}

def is_high_risk(tool: str, action: str) -> bool:
    """Check if tool.action combo is high-risk."""
    if tool in HIGH_RISK_ACTIONS:
        return action in HIGH_RISK_ACTIONS[tool]
    return False

def get_risk_description(tool: str, action: str) -> str:
    """Get human-readable risk description."""
    key = f"{tool}.{action}"
    return RISK_DESCRIPTIONS.get(key, f"Execute {action} on {tool}")
