"""
Formatter - Formats agent response for user.
"""
from typing import Dict, Any
from core.parser import Intent, ParsedIntent

def format_reply(parsed: ParsedIntent, result: Dict[str, Any], verify: Dict[str, Any]) -> str:
    """Format the final reply based on intent, result, and verification."""
    
    if result.get("needs_approval"):
        pending = result.get("pending_approvals", [])
        lines = ["⚠️ Action requires approval\n"]
        for p in pending:
            lines.append(f"• {p['description']}")
            lines.append(f"  To approve, type: APPROVE {p['approval_id']}\n")
        return "\n".join(lines)
    
    if not verify.get("ok"):
        issues = verify.get("issues", [])
        return f"⚠️ Something went wrong:\n" + "\n".join(f"• {i}" for i in issues)
    
    if result.get("fallback") == "unknown_intent":
        return (
            f"🤖 I didn't understand: \"{result.get('original_text', '')}\"\n\n"
            "Try:\n• add task <title>\n• run <command>\n• buka <app>\n• ls <path>\n• baca file <path>"
        )
    
    results = result.get("results", [])
    if not results:
        return "✅ Done."
    
    first_result = results[0].get("result", {})
    
    # Task responses
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
        return f"⚠️ Task not found."
    
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
    
    # Preference responses
    elif parsed.intent == Intent.MY_PREFS:
        return first_result.get("display", "No preferences found.")
    
    elif parsed.intent == Intent.SET_PREF:
        if first_result.get("success"):
            return f"✅ Preference updated: {first_result.get('key')} = {first_result.get('value')}"
        return f"⚠️ {first_result.get('error')}"
    
    # Proposal responses
    elif parsed.intent == Intent.LIST_PROPOSALS:
        return first_result.get("display", "No proposals found.")
    
    elif parsed.intent == Intent.APPROVE_PROPOSAL:
        if first_result.get("success"):
            return f"✅ Proposal #{first_result.get('proposal_id')} approved. Rule #{first_result.get('rule_id')} created."
        return f"⚠️ {first_result.get('error')}"
    
    elif parsed.intent == Intent.REJECT_PROPOSAL:
        if first_result.get("success"):
            return f"✅ Proposal #{first_result.get('proposal_id')} rejected."
        return f"⚠️ {first_result.get('error')}"
    
    elif parsed.intent == Intent.ROLLBACK_PROPOSAL:
        if first_result.get("success"):
            return f"↩️ Proposal #{first_result.get('proposal_id')} rolled back."
        return f"⚠️ {first_result.get('error')}"
    
    # Computer use responses
    elif parsed.intent == Intent.RUN_COMMAND:
        if first_result.get("success"):
            stdout = first_result.get("stdout", "")
            output = stdout[:2000] if stdout else "(no output)"
            return f"✅ Command executed:\n```\n{output}\n```"
        return f"⚠️ Command failed: {first_result.get('stderr') or first_result.get('error')}"
    
    elif parsed.intent == Intent.READ_FILE:
        if first_result.get("success"):
            content = first_result.get("content", "")
            preview = content[:1500] + "..." if len(content) > 1500 else content
            return f"📄 **{first_result.get('path')}** ({first_result.get('size')} bytes):\n```\n{preview}\n```"
        return f"⚠️ {first_result.get('error')}"
    
    elif parsed.intent == Intent.LIST_FILES:
        if first_result.get("success"):
            entries = first_result.get("entries", [])
            if not entries:
                return "📁 Empty directory."
            lines = ["📁 **Files:**"]
            for e in entries[:30]:  # Limit to 30 entries
                icon = "📂" if e["is_dir"] else "📄"
                size = f" ({e['size']} bytes)" if not e["is_dir"] else ""
                lines.append(f"  {icon} {e['name']}{size}")
            if len(entries) > 30:
                lines.append(f"  ... and {len(entries) - 30} more")
            return "\n".join(lines)
        return f"⚠️ {first_result.get('error')}"
    
    elif parsed.intent == Intent.OPEN_APP:
        if first_result.get("success"):
            return f"✅ {first_result.get('message')}"
        return f"⚠️ {first_result.get('error')}"
    
    elif parsed.intent == Intent.CLOSE_APP:
        if first_result.get("success"):
            return f"✅ {first_result.get('message')}"
        return f"⚠️ {first_result.get('error')}"
    
    elif parsed.intent == Intent.SCREENSHOT:
        if first_result.get("success"):
            return f"📸 Screenshot saved to: {first_result.get('path')}"
        return f"⚠️ {first_result.get('error')}"
    
    return "✅ Done."
