"""
UI Tool - Mouse, keyboard, and screen interaction using pyautogui.
⚠️ HIGH RISK - All actions require approval.
"""
import pyautogui
import os
import time
from typing import Dict, Any
from core.logging_config import get_logger

logger = get_logger(__name__)

# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.5  # Pause between actions

SCREENSHOT_DIR = os.path.expanduser("/Users/ibnufajar/Documents/screenshoot")

def execute(action: str, params: Dict[str, Any], user_id: int, db) -> Dict[str, Any]:
    """
    Execute UI automation actions.
    Actions: screenshot, click, type, scroll, hotkey, search
    """
    
    if action == "screenshot":
        try:
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            filename = f"screenshot_{int(time.time())}.png"
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
            
            # Default is NOT silent (send photo) unless silent=True
            silent = params.get("silent", False)
            
            return {
                "success": True, 
                "path": filepath,
                "send_photo": not silent,  # Only send if not silent
                "message": "Screenshot captured"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "click":
        x = params.get("x")
        y = params.get("y")
        
        if x is None or y is None:
            return {"success": False, "error": "x and y coordinates required"}
        
        try:
            pyautogui.click(x, y)
            logger.info(f"Clicked at ({x}, {y})")
            return {"success": True, "message": f"Clicked at ({x}, {y})"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "type":
        text = params.get("text", "")
        if not text:
            return {"success": False, "error": "Text required"}
        
        try:
            # Small delay before typing
            time.sleep(0.3)
            pyautogui.typewrite(text, interval=0.05) if text.isascii() else pyautogui.write(text)
            logger.info(f"Typed: {text[:50]}...")
            return {"success": True, "message": f"Typed text"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "hotkey":
        keys = params.get("keys", [])
        if not keys:
            return {"success": False, "error": "Keys required (e.g., ['command', 'c'])"}
        
        try:
            pyautogui.hotkey(*keys)
            logger.info(f"Pressed hotkey: {'+'.join(keys)}")
            return {"success": True, "message": f"Pressed {'+'.join(keys)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "scroll":
        direction = params.get("direction", "down")
        amount = params.get("amount", 3)
        
        try:
            clicks = amount if direction == "up" else -amount
            pyautogui.scroll(clicks)
            logger.info(f"Scrolled {direction} {amount} clicks")
            return {"success": True, "message": f"Scrolled {direction}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "search":
        # Open Spotlight and search
        query = params.get("query", "")
        if not query:
            return {"success": False, "error": "Search query required"}
        
        try:
            pyautogui.hotkey("command", "space")
            time.sleep(0.5)
            pyautogui.typewrite(query, interval=0.05) if query.isascii() else None
            time.sleep(0.3)
            pyautogui.press("enter")
            
            logger.info(f"Searched for: {query}")
            return {"success": True, "message": f"Searched for '{query}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "move":
        x = params.get("x")
        y = params.get("y")
        
        if x is None or y is None:
            return {"success": False, "error": "x and y coordinates required"}
        
        try:
            pyautogui.moveTo(x, y, duration=0.3)
            return {"success": True, "message": f"Moved to ({x}, {y})"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    elif action == "press":
        key = params.get("key", "")
        if not key:
            return {"success": False, "error": "Key required"}
        
        try:
            pyautogui.press(key)
            return {"success": True, "message": f"Pressed {key}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    else:
        return {"success": False, "error": f"Unknown UI action: {action}"}

def get_screen_size() -> Dict[str, int]:
    """Get screen dimensions."""
    width, height = pyautogui.size()
    return {"width": width, "height": height}
