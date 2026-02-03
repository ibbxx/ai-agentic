"""
Safety Configuration - Limits and timeouts for agent execution.
"""

# Maximum steps per agent run
MAX_STEPS_PER_RUN = 6

# Tool execution timeout in seconds
TOOL_TIMEOUT_SECONDS = 30

# Maximum LLM tokens per request
MAX_LLM_TOKENS = 500

# Maximum plan depth (nested tools)
MAX_PLAN_DEPTH = 3

# Rate limiting
RATE_LIMIT_REQUESTS = 20  # Max requests
RATE_LIMIT_WINDOW = 60    # Per 60 seconds

# Blocked patterns in user input
BLOCKED_INPUT_PATTERNS = [
    "sudo", "rm -rf", "DROP TABLE", "DELETE FROM",
    "<script>", "javascript:", "eval(", "exec(",
]

def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input for blocked patterns."""
    if not text:
        return True, ""
    
    text_lower = text.lower()
    for pattern in BLOCKED_INPUT_PATTERNS:
        if pattern.lower() in text_lower:
            return False, f"Blocked pattern detected: {pattern}"
    
    # Length limit
    if len(text) > 4000:
        return False, "Message too long (max 4000 characters)"
    
    return True, ""
