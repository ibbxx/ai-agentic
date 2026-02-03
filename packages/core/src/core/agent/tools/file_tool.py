"""
File Tool - Read, write, and manage files on the local machine.
⚠️ HIGH RISK - Write/delete actions require approval.
"""
import os
import shutil
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.logging_config import get_logger

logger = get_logger(__name__)

MAX_READ_SIZE = 100000  # 100KB max read
MAX_WRITE_SIZE = 50000  # 50KB max write

# Protected paths (cannot modify)
PROTECTED_PATHS = [
    "/System", "/usr", "/bin", "/sbin", "/etc",
    "/Library/System", "/private/var",
    os.path.expanduser("~/.ssh"),
    os.path.expanduser("~/.gnupg"),
]

def is_protected_path(path: str) -> bool:
    """Check if path is protected."""
    abs_path = os.path.abspath(os.path.expanduser(path))
    for protected in PROTECTED_PATHS:
        if abs_path.startswith(protected):
            return True
    return False

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute file-related actions.
    Actions: read, write, list, exists, delete, mkdir, copy, move
    """
    path = params.get("path", "")
    if path:
        path = os.path.expanduser(path)
    
    if action == "read":
        if not path:
            return {"success": False, "error": "No path provided"}
        
        try:
            if not os.path.exists(path):
                return {"success": False, "error": f"File not found: {path}"}
            
            size = os.path.getsize(path)
            if size > MAX_READ_SIZE:
                return {"success": False, "error": f"File too large ({size} bytes). Max: {MAX_READ_SIZE}"}
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return {"success": True, "content": content, "size": size, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "write":
        content = params.get("content", "")
        
        if not path:
            return {"success": False, "error": "No path provided"}
        
        if is_protected_path(path):
            return {"success": False, "error": "Cannot write to protected path"}
        
        if len(content) > MAX_WRITE_SIZE:
            return {"success": False, "error": f"Content too large. Max: {MAX_WRITE_SIZE} bytes"}
        
        try:
            # Create parent dirs if needed
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Wrote {len(content)} bytes to {path}")
            return {"success": True, "path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "list":
        if not path:
            path = "."
        
        try:
            entries = []
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                is_dir = os.path.isdir(full_path)
                size = os.path.getsize(full_path) if not is_dir else 0
                entries.append({
                    "name": entry,
                    "is_dir": is_dir,
                    "size": size
                })
            
            return {"success": True, "entries": entries, "count": len(entries)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "exists":
        if not path:
            return {"success": False, "error": "No path provided"}
        
        exists = os.path.exists(path)
        is_file = os.path.isfile(path) if exists else False
        is_dir = os.path.isdir(path) if exists else False
        
        return {"success": True, "exists": exists, "is_file": is_file, "is_dir": is_dir}
    
    elif action == "delete":
        if not path:
            return {"success": False, "error": "No path provided"}
        
        if is_protected_path(path):
            return {"success": False, "error": "Cannot delete protected path"}
        
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            else:
                return {"success": False, "error": f"Path not found: {path}"}
            
            logger.info(f"Deleted: {path}")
            return {"success": True, "deleted": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "mkdir":
        if not path:
            return {"success": False, "error": "No path provided"}
        
        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True, "created": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "copy":
        dest = params.get("dest", "")
        if not path or not dest:
            return {"success": False, "error": "Source and destination required"}
        
        dest = os.path.expanduser(dest)
        
        if is_protected_path(dest):
            return {"success": False, "error": "Cannot copy to protected path"}
        
        try:
            if os.path.isfile(path):
                shutil.copy2(path, dest)
            else:
                shutil.copytree(path, dest)
            return {"success": True, "source": path, "dest": dest}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "move":
        dest = params.get("dest", "")
        if not path or not dest:
            return {"success": False, "error": "Source and destination required"}
        
        dest = os.path.expanduser(dest)
        
        if is_protected_path(path) or is_protected_path(dest):
            return {"success": False, "error": "Cannot move protected path"}
        
        try:
            shutil.move(path, dest)
            return {"success": True, "source": path, "dest": dest}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "send":
        # Prepare file for sending to Telegram
        if not path:
            return {"success": False, "error": "No path provided"}
        
        try:
            if not os.path.exists(path):
                return {"success": False, "error": f"File not found: {path}"}
            
            if not os.path.isfile(path):
                return {"success": False, "error": "Can only send files, not directories"}
            
            size = os.path.getsize(path)
            # Telegram limit is 50MB
            if size > 50 * 1024 * 1024:
                return {"success": False, "error": f"File too large ({size} bytes). Telegram max: 50MB"}
            
            # Return path for handler to send
            return {
                "success": True, 
                "path": path,
                "filename": os.path.basename(path),
                "size": size,
                "send_file": True  # Flag for handler
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "find_latest":
        # Find the most recent file in a directory
        if not path:
            return {"success": False, "error": "No directory path provided"}
        
        try:
            if not os.path.isdir(path):
                return {"success": False, "error": f"Not a directory: {path}"}
            
            files = []
            for f in os.listdir(path):
                full_path = os.path.join(path, f)
                if os.path.isfile(full_path):
                    files.append((full_path, os.path.getmtime(full_path)))
            
            if not files:
                return {"success": False, "error": "No files in directory"}
            
            # Sort by modification time, newest first
            files.sort(key=lambda x: x[1], reverse=True)
            latest = files[0][0]
            
            return {
                "success": True,
                "path": latest,
                "filename": os.path.basename(latest),
                "size": os.path.getsize(latest),
                "send_file": True  # Flag for handler to send
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    else:
        return {"success": False, "error": f"Unknown file action: {action}"}
