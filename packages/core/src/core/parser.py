"""
Intent Parser - Robust command parsing for agent messages.
Supports: add task, list tasks, done, daily brief, approve
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
        title = text.strip()[len("add task "):].strip()  # Preserve original case for title
        return ParsedIntent(intent=Intent.ADD_TASK, params={"title": title})
    
    # Pattern: list tasks
    if normalized in ["list tasks", "list task", "tasks", "show tasks"]:
        return ParsedIntent(intent=Intent.LIST_TASKS, params={})
    
    # Pattern: done <id> or close <id> or complete <id>
    done_match = re.match(r'^(done|close|complete)\s+(\d+)$', normalized)
    if done_match:
        task_id = int(done_match.group(2))
        return ParsedIntent(intent=Intent.DONE_TASK, params={"task_id": task_id})
    
    # Pattern: delete task <id> (HIGH RISK)
    delete_match = re.match(r'^delete\s+task\s+(\d+)$', normalized)
    if delete_match:
        task_id = int(delete_match.group(1))
        return ParsedIntent(intent=Intent.DELETE_TASK, params={"task_id": task_id})
    
    # Pattern: daily brief
    if normalized in ["daily brief", "brief", "daily", "morning brief"]:
        return ParsedIntent(intent=Intent.DAILY_BRIEF, params={})
    
    # Pattern: approve <id>
    approve_match = re.match(r'^approve\s+(\d+)$', normalized)
    if approve_match:
        approval_id = int(approve_match.group(1))
        return ParsedIntent(intent=Intent.APPROVE, params={"approval_id": approval_id})
    
    return ParsedIntent(intent=Intent.UNKNOWN, params={"text": text.strip()})
