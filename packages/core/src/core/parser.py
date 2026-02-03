"""
Intent Parser - Robust command parsing for agent messages.
Supports: add task, list tasks, done, daily brief, approve, delete task, my prefs, set brief time, proposals
"""
import re
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class Intent(str, Enum):
    ADD_TASK = "add_task"
    LIST_TASKS = "list_tasks"
    DONE_TASK = "done_task"
    DELETE_TASK = "delete_task"
    DAILY_BRIEF = "daily_brief"
    APPROVE = "approve"
    MY_PREFS = "my_prefs"
    SET_PREF = "set_pref"
    LIST_PROPOSALS = "list_proposals"
    APPROVE_PROPOSAL = "approve_proposal"
    REJECT_PROPOSAL = "reject_proposal"
    ROLLBACK_PROPOSAL = "rollback_proposal"
    UNKNOWN = "unknown"

@dataclass
class ParsedIntent:
    intent: Intent
    params: dict

def parse_message(text: str) -> ParsedIntent:
    """
    Parse user message to extract intent and parameters.
    Case-insensitive, handles extra whitespace.
    """
    if not text:
        return ParsedIntent(intent=Intent.UNKNOWN, params={})
    
    # Normalize: lowercase, strip, collapse whitespace
    normalized = " ".join(text.strip().lower().split())
    
    # Pattern: add task <title>
    add_task_match = re.match(r'^add\s+task\s+(.+)$', normalized)
    if add_task_match:
        title = text.strip()[len("add task "):].strip()
        return ParsedIntent(intent=Intent.ADD_TASK, params={"title": title})
    
    # Pattern: list tasks
    if normalized in ["list tasks", "list task", "tasks", "show tasks"]:
        return ParsedIntent(intent=Intent.LIST_TASKS, params={})
    
    # Pattern: done <id> or close <id> or complete <id>
    done_match = re.match(r'^(done|close|complete)\s+(\d+)$', normalized)
    if done_match:
        task_id = int(done_match.group(2))
        return ParsedIntent(intent=Intent.DONE_TASK, params={"task_id": task_id})
    
    # Pattern: delete task <id>
    delete_match = re.match(r'^delete\s+task\s+(\d+)$', normalized)
    if delete_match:
        task_id = int(delete_match.group(1))
        return ParsedIntent(intent=Intent.DELETE_TASK, params={"task_id": task_id})
    
    # Pattern: daily brief
    if normalized in ["daily brief", "brief", "daily", "morning brief"]:
        return ParsedIntent(intent=Intent.DAILY_BRIEF, params={})
    
    # Pattern: approve <id> (for approvals)
    approve_match = re.match(r'^approve\s+(\d+)$', normalized)
    if approve_match:
        approval_id = int(approve_match.group(1))
        return ParsedIntent(intent=Intent.APPROVE, params={"approval_id": approval_id})
    
    # Pattern: my prefs / preferences / settings
    if normalized in ["my prefs", "my preferences", "preferences", "settings", "my settings"]:
        return ParsedIntent(intent=Intent.MY_PREFS, params={})
    
    # Pattern: set brief time <HH:MM>
    brief_time_match = re.match(r'^set\s+brief\s+time\s+(\d{1,2}):?(\d{2})$', normalized)
    if brief_time_match:
        hour = int(brief_time_match.group(1))
        minute = int(brief_time_match.group(2))
        time_str = f"{hour:02d}:{minute:02d}"
        return ParsedIntent(intent=Intent.SET_PREF, params={"key": "brief_time", "value": time_str})
    
    # Pattern: set timezone <tz>
    tz_match = re.match(r'^set\s+timezone\s+(.+)$', normalized)
    if tz_match:
        tz = tz_match.group(1).strip()
        return ParsedIntent(intent=Intent.SET_PREF, params={"key": "timezone", "value": tz})
    
    # Pattern: set brief format <format>
    format_match = re.match(r'^set\s+brief\s+format\s+(detailed|compact|minimal)$', normalized)
    if format_match:
        fmt = format_match.group(1)
        return ParsedIntent(intent=Intent.SET_PREF, params={"key": "brief_format", "value": fmt})
    
    # Pattern: proposals / list proposals
    if normalized in ["proposals", "list proposals", "show proposals", "my proposals"]:
        return ParsedIntent(intent=Intent.LIST_PROPOSALS, params={})
    
    # Pattern: approve proposal <id>
    approve_proposal_match = re.match(r'^approve\s+proposal\s+(\d+)$', normalized)
    if approve_proposal_match:
        proposal_id = int(approve_proposal_match.group(1))
        return ParsedIntent(intent=Intent.APPROVE_PROPOSAL, params={"proposal_id": proposal_id})
    
    # Pattern: reject proposal <id>
    reject_proposal_match = re.match(r'^reject\s+proposal\s+(\d+)$', normalized)
    if reject_proposal_match:
        proposal_id = int(reject_proposal_match.group(1))
        return ParsedIntent(intent=Intent.REJECT_PROPOSAL, params={"proposal_id": proposal_id})
    
    # Pattern: rollback proposal <id>
    rollback_match = re.match(r'^rollback\s+proposal\s+(\d+)$', normalized)
    if rollback_match:
        proposal_id = int(rollback_match.group(1))
        return ParsedIntent(intent=Intent.ROLLBACK_PROPOSAL, params={"proposal_id": proposal_id})
    
    return ParsedIntent(intent=Intent.UNKNOWN, params={"text": text.strip()})
