"""
Shell Tool - Execute terminal commands on the local machine.
⚠️ HIGH RISK - All actions require approval.
"""
import subprocess
import os
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.logging_config import get_logger

logger = get_logger(__name__)

# Allowed commands whitelist (safe commands that don't need approval)
SAFE_COMMANDS = [
    "ls", "pwd", "whoami", "date", "cal", "echo",
    "cat", "head", "tail", "wc", "which", "whereis",
]

# Blocked commands (never execute even with approval)
BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf ~", "rm -rf *",
    "sudo rm", "mkfs", "dd if=",
    ":(){ :|:& };:", # fork bomb
    "> /dev/sda", "chmod -R 777 /",
]

MAX_OUTPUT_LENGTH = 10000  # Limit output size
TIMEOUT_SECONDS = 30

def is_safe_command(cmd: str) -> bool:
    """Check if command is in safe whitelist."""
    cmd_lower = cmd.strip().lower()
    base_cmd = cmd_lower.split()[0] if cmd_lower else ""
    return base_cmd in SAFE_COMMANDS

def is_blocked_command(cmd: str) -> bool:
    """Check if command is in blocked list."""
    cmd_lower = cmd.strip().lower()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return True
    return False

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute shell-related actions.
    Actions: run, pwd, ls
    """
    if action == "run":
        command = params.get("command", "")
        cwd = params.get("cwd", os.path.expanduser("~"))
        
        if not command:
            return {"success": False, "error": "No command provided"}
        
        if is_blocked_command(command):
            return {"success": False, "error": "Command is blocked for safety"}
        
        logger.info(f"Executing shell command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS
            )
            
            stdout = result.stdout[:MAX_OUTPUT_LENGTH] if result.stdout else ""
            stderr = result.stderr[:MAX_OUTPUT_LENGTH] if result.stderr else ""
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {TIMEOUT_SECONDS}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "pwd":
        return {"success": True, "cwd": os.getcwd()}
    
    elif action == "ls":
        path = params.get("path", ".")
        try:
            files = os.listdir(os.path.expanduser(path))
            return {"success": True, "files": files, "count": len(files)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    else:
        return {"success": False, "error": f"Unknown shell action: {action}"}
