"""
Intent Parser - Robust command parsing for agent messages.
Supports: tasks, preferences, proposals, computer use (shell, file, app)
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
    # Computer use
    RUN_COMMAND = "run_command"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    LIST_FILES = "list_files"
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    SCREENSHOT = "screenshot"
    UNKNOWN = "unknown"

@dataclass
class ParsedIntent:
    intent: Intent
    params: dict

def parse_message(text: str) -> ParsedIntent:
    """Parse user message to extract intent and parameters."""
    if not text:
        return ParsedIntent(intent=Intent.UNKNOWN, params={})
    
    normalized = " ".join(text.strip().lower().split())
    
    # === TASK COMMANDS ===
    add_task_match = re.match(r'^add\s+task\s+(.+)$', normalized)
    if add_task_match:
        title = text.strip()[len("add task "):].strip()
        return ParsedIntent(intent=Intent.ADD_TASK, params={"title": title})
    
    if normalized in ["list tasks", "list task", "tasks", "show tasks"]:
        return ParsedIntent(intent=Intent.LIST_TASKS, params={})
    
    done_match = re.match(r'^(done|close|complete)\s+(\d+)$', normalized)
    if done_match:
        return ParsedIntent(intent=Intent.DONE_TASK, params={"task_id": int(done_match.group(2))})
    
    delete_match = re.match(r'^delete\s+task\s+(\d+)$', normalized)
    if delete_match:
        return ParsedIntent(intent=Intent.DELETE_TASK, params={"task_id": int(delete_match.group(1))})
    
    if normalized in ["daily brief", "brief", "daily", "morning brief"]:
        return ParsedIntent(intent=Intent.DAILY_BRIEF, params={})
    
    approve_match = re.match(r'^approve\s+(\d+)$', normalized)
    if approve_match:
        return ParsedIntent(intent=Intent.APPROVE, params={"approval_id": int(approve_match.group(1))})
    
    # === PREFERENCE COMMANDS ===
    if normalized in ["my prefs", "my preferences", "preferences", "settings", "my settings"]:
        return ParsedIntent(intent=Intent.MY_PREFS, params={})
    
    brief_time_match = re.match(r'^set\s+brief\s+time\s+(\d{1,2}):?(\d{2})$', normalized)
    if brief_time_match:
        time_str = f"{int(brief_time_match.group(1)):02d}:{brief_time_match.group(2)}"
        return ParsedIntent(intent=Intent.SET_PREF, params={"key": "brief_time", "value": time_str})
    
    # === PROPOSAL COMMANDS ===
    if normalized in ["proposals", "list proposals", "show proposals", "my proposals"]:
        return ParsedIntent(intent=Intent.LIST_PROPOSALS, params={})
    
    approve_proposal_match = re.match(r'^approve\s+proposal\s+(\d+)$', normalized)
    if approve_proposal_match:
        return ParsedIntent(intent=Intent.APPROVE_PROPOSAL, params={"proposal_id": int(approve_proposal_match.group(1))})
    
    reject_proposal_match = re.match(r'^reject\s+proposal\s+(\d+)$', normalized)
    if reject_proposal_match:
        return ParsedIntent(intent=Intent.REJECT_PROPOSAL, params={"proposal_id": int(reject_proposal_match.group(1))})
    
    rollback_match = re.match(r'^rollback\s+proposal\s+(\d+)$', normalized)
    if rollback_match:
        return ParsedIntent(intent=Intent.ROLLBACK_PROPOSAL, params={"proposal_id": int(rollback_match.group(1))})
    
    # === COMPUTER USE COMMANDS ===
    
    # Run command: "run <cmd>", "jalankan <cmd>", "execute <cmd>"
    run_match = re.match(r'^(run|jalankan|execute|exec)\s+(.+)$', normalized)
    if run_match:
        return ParsedIntent(intent=Intent.RUN_COMMAND, params={"command": run_match.group(2)})
    
    # Read file: "read file <path>", "baca file <path>", "cat <path>"
    read_match = re.match(r'^(read file|baca file|baca|cat)\s+(.+)$', normalized)
    if read_match:
        return ParsedIntent(intent=Intent.READ_FILE, params={"path": read_match.group(2).strip()})
    
    # List files: "ls <path>", "list files <path>"
    ls_match = re.match(r'^(ls|list files|lihat folder|lihat)\s*(.*)$', normalized)
    if ls_match:
        path = ls_match.group(2).strip() or "."
        return ParsedIntent(intent=Intent.LIST_FILES, params={"path": path})
    
    # Open app: "buka <app>", "open <app>", "buka <site> di <browser>"
    open_match = re.match(r'^(buka|open)\s+(.+)$', normalized)
    if open_match:
        app_and_file = open_match.group(2).strip()
        
        # If contains multi-step keywords, route to LLM
        multi_step_keywords = ['lalu', 'terus', 'kemudian', 'kirimkan', 'kirim', 'cari', 'search', 'download']
        if any(kw in app_and_file for kw in multi_step_keywords):
            return ParsedIntent(intent=Intent.UNKNOWN, params={"text": text.strip()})
        
        # Pattern: "buka pinterest di chrome" → open chrome with URL pinterest.com
        di_match = re.match(r'^(.+?)\s+di\s+(chrome|firefox|safari|browser)$', app_and_file, re.IGNORECASE)
        if di_match:
            site = di_match.group(1).strip()
            browser = di_match.group(2).strip()
            # Add .com if no TLD
            if "." not in site:
                site = f"https://{site}.com"
            elif not site.startswith("http"):
                site = f"https://{site}"
            return ParsedIntent(intent=Intent.OPEN_APP, params={"app": browser, "url": site})
        
        # Simple app open (no "dan")
        if " dan " not in app_and_file:
            return ParsedIntent(intent=Intent.OPEN_APP, params={"app": app_and_file})
        
        # Contains "dan" = likely complex, route to LLM
        return ParsedIntent(intent=Intent.UNKNOWN, params={"text": text.strip()})
    
    # Close app: "tutup <app>", "close <app>"
    close_match = re.match(r'^(tutup|close)\s+(.+)$', normalized)
    if close_match:
        return ParsedIntent(intent=Intent.CLOSE_APP, params={"app": close_match.group(2).strip()})
    
    # Screenshot
    if normalized in ["screenshot", "ss", "tangkap layar", "screencapture"]:
        return ParsedIntent(intent=Intent.SCREENSHOT, params={})
    
    return ParsedIntent(intent=Intent.UNKNOWN, params={"text": text.strip()})
