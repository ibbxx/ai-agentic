"""
App Tool - Open, close, and control applications on macOS.
⚠️ HIGH RISK - All actions require approval.
"""
import subprocess
import os
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.logging_config import get_logger

logger = get_logger(__name__)

# Common app mappings
APP_ALIASES = {
    "chrome": "Google Chrome",
    "firefox": "Firefox",
    "safari": "Safari",
    "cursor": "Cursor",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code",
    "terminal": "Terminal",
    "iterm": "iTerm",
    "finder": "Finder",
    "notes": "Notes",
    "music": "Music",
    "spotify": "Spotify",
    "slack": "Slack",
    "discord": "Discord",
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
}

def resolve_app_name(name: str) -> str:
    """Resolve app alias to full name."""
    lower_name = name.lower().strip()
    return APP_ALIASES.get(lower_name, name)

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute app-related actions.
    Actions: open, close, list, focus
    """
    if action == "open":
        app_name = params.get("app", "")
        if not app_name:
            return {"success": False, "error": "No app name provided"}
        
        app_name = resolve_app_name(app_name)
        
        # Check if opening a file/URL
        file_path = params.get("file", "")
        url = params.get("url", "")
        
        try:
            if file_path:
                # Open file with app
                file_path = os.path.expanduser(file_path)
                result = subprocess.run(
                    ["open", "-a", app_name, file_path],
                    capture_output=True, text=True, timeout=10
                )
            elif url:
                # Open URL with app
                result = subprocess.run(
                    ["open", "-a", app_name, url],
                    capture_output=True, text=True, timeout=10
                )
            else:
                # Just open the app
                result = subprocess.run(
                    ["open", "-a", app_name],
                    capture_output=True, text=True, timeout=10
                )
            
            if result.returncode == 0:
                logger.info(f"Opened app: {app_name}")
                return {"success": True, "app": app_name, "message": f"Opened {app_name}"}
            else:
                return {"success": False, "error": result.stderr or "Failed to open app"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "close":
        app_name = params.get("app", "")
        if not app_name:
            return {"success": False, "error": "No app name provided"}
        
        app_name = resolve_app_name(app_name)
        
        try:
            # Use AppleScript to quit app gracefully
            script = f'tell application "{app_name}" to quit'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Closed app: {app_name}")
                return {"success": True, "app": app_name, "message": f"Closed {app_name}"}
            else:
                return {"success": False, "error": result.stderr or "Failed to close app"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "list":
        try:
            # List running apps using AppleScript
            script = '''
            tell application "System Events"
                set appList to name of every process whose background only is false
            end tell
            return appList
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                apps = [app.strip() for app in result.stdout.split(",")]
                return {"success": True, "running_apps": apps, "count": len(apps)}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "focus":
        app_name = params.get("app", "")
        if not app_name:
            return {"success": False, "error": "No app name provided"}
        
        app_name = resolve_app_name(app_name)
        
        try:
            script = f'tell application "{app_name}" to activate'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                return {"success": True, "app": app_name, "message": f"Focused {app_name}"}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "screenshot":
        output_path = params.get("path", os.path.expanduser("~/Desktop/screenshot.png"))
        
        try:
            result = subprocess.run(
                ["screencapture", "-x", output_path],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                return {"success": True, "path": output_path, "message": "Screenshot saved"}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    else:
        return {"success": False, "error": f"Unknown app action: {action}"}
