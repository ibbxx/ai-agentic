"""
Formatter - Formats agent response for user.
"""
from typing import Dict, Any
from core.parser import Intent, ParsedIntent

def format_reply(parsed: ParsedIntent, result: Dict[str, Any], verify: Dict[str, Any]) -> str:
    """
    Format the final reply based on intent, result, and verification.
    """
    # Handle pending approvals first
    if result.get("needs_approval"):
        pending = result.get("pending_approvals", [])
        lines = ["⚠️ **Action requires approval**\n"]
        for p in pending:
            lines.append(f"• {p['description']}")
            lines.append(f"  To approve, type: `APPROVE {p['approval_id']}`\n")
        return "\n".join(lines)
    
    if not verify.get("ok"):
        issues = verify.get("issues", [])
        return f"⚠️ Something went wrong:\n" + "\n".join(f"• {i}" for i in issues)
    
    # Handle fallback for unknown intent
    if result.get("fallback") == "unknown_intent":
        original = result.get("original_text", "")
        return (
            f"🤖 I didn't understand: \"{original}\"\n\n"
            "Try:\n• add task <title>\n• list tasks\n• done <id>\n• daily brief\n• approve <id>"
        )
    
    # Extract first result for simple single-step plans
    results = result.get("results", [])
    if not results:
        return "✅ Done."
    
    first_result = results[0].get("result", {})
    
    if parsed.intent == Intent.ADD_TASK:
        task_id = first_result.get("task_id")
        title = first_result.get("title")
        return f"✅ Task added: #{task_id} - {title}"
    
    elif parsed.intent == Intent.LIST_TASKS:
        tasks = first_result.get("tasks", [])
        if not tasks:
            return "📋 No open tasks."
        task_list = "\n".join([f"  {t['id']}. {t['title']}" for t in tasks])
        return f"📋 Open Tasks:\n{task_list}"
    
    elif parsed.intent == Intent.DONE_TASK:
        task_id = first_result.get("task_id")
        if first_result.get("success"):
            return f"✅ Task #{task_id} marked as done."
        else:
            return f"⚠️ Task #{task_id} not found."
    
    elif parsed.intent == Intent.DAILY_BRIEF:
        tasks = first_result.get("tasks", [])
        if not tasks:
            return "☀️ Good morning! You have no open tasks."
        task_list = "\n".join([f"  - {t['title']}" for t in tasks])
        return f"☀️ Daily Brief:\n\nOpen Tasks ({len(tasks)}):\n{task_list}"
    
    elif parsed.intent == Intent.APPROVE:
        approval_id = first_result.get("approval_id")
        if first_result.get("success"):
            return f"✅ Request #{approval_id} approved and executed."
        else:
            return f"⚠️ {first_result.get('error', 'Unknown error')}"
    
    return "✅ Done."
