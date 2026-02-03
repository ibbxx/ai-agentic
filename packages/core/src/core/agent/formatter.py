"""
Formatter - Formats agent response for user.
"""
from typing import Dict, Any
from core.parser import Intent, ParsedIntent

def format_reply(parsed: ParsedIntent, result: Dict[str, Any], verify: Dict[str, Any]) -> str:
    """Format the final reply based on intent, result, and verification."""
    
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
    
    if result.get("fallback") == "unknown_intent":
        return (
            f"🤖 I didn't understand: \"{result.get('original_text', '')}\"\n\n"
            "Try:\n• add task <title>\n• list tasks\n• done <id>\n• daily brief\n• my prefs\n• proposals"
        )
    
    results = result.get("results", [])
    if not results:
        return "✅ Done."
    
    first_result = results[0].get("result", {})
    
    if parsed.intent == Intent.ADD_TASK:
        return f"✅ Task added: #{first_result.get('task_id')} - {first_result.get('title')}"
    
    elif parsed.intent == Intent.LIST_TASKS:
        tasks = first_result.get("tasks", [])
        if not tasks:
            return "📋 No open tasks."
        task_list = "\n".join([f"  {t['id']}. {t['title']}" for t in tasks])
        return f"📋 Open Tasks:\n{task_list}"
    
    elif parsed.intent == Intent.DONE_TASK:
        if first_result.get("success"):
            return f"✅ Task #{first_result.get('task_id')} marked as done."
        return f"⚠️ Task #{first_result.get('task_id')} not found."
    
    elif parsed.intent == Intent.DAILY_BRIEF:
        tasks = first_result.get("tasks", [])
        if not tasks:
            return "☀️ Good morning! You have no open tasks."
        task_list = "\n".join([f"  - {t['title']}" for t in tasks])
        return f"☀️ Daily Brief:\n\nOpen Tasks ({len(tasks)}):\n{task_list}"
    
    elif parsed.intent == Intent.APPROVE:
        if first_result.get("success"):
            return f"✅ Request #{first_result.get('approval_id')} approved and executed."
        return f"⚠️ {first_result.get('error', 'Unknown error')}"
    
    elif parsed.intent == Intent.MY_PREFS:
        return first_result.get("display", "No preferences found.")
    
    elif parsed.intent == Intent.SET_PREF:
        if first_result.get("success"):
            return f"✅ Preference updated: {first_result.get('key')} = {first_result.get('value')}"
        return f"⚠️ {first_result.get('error', 'Failed to update preference')}"
    
    elif parsed.intent == Intent.LIST_PROPOSALS:
        return first_result.get("display", "No proposals found.")
    
    elif parsed.intent == Intent.APPROVE_PROPOSAL:
        if first_result.get("success"):
            return f"✅ Proposal #{first_result.get('proposal_id')} approved. Rule #{first_result.get('rule_id')} created."
        return f"⚠️ {first_result.get('error', 'Failed to approve proposal')}"
    
    elif parsed.intent == Intent.REJECT_PROPOSAL:
        if first_result.get("success"):
            return f"✅ Proposal #{first_result.get('proposal_id')} rejected."
        return f"⚠️ {first_result.get('error', 'Failed to reject proposal')}"
    
    elif parsed.intent == Intent.ROLLBACK_PROPOSAL:
        if first_result.get("success"):
            return f"↩️ Proposal #{first_result.get('proposal_id')} rolled back. {first_result.get('rules_deactivated', 0)} rules deactivated."
        return f"⚠️ {first_result.get('error', 'Failed to rollback proposal')}"
    
    return "✅ Done."
