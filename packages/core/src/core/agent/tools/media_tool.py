"""
Media Tool - Handle media playback (YouTube, Spotify, etc).
"""
import subprocess
import httpx
import re
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.logging_config import get_logger

logger = get_logger(__name__)

def get_video_id(query: str) -> str:
    """Search YouTube and return first video ID."""
    try:
        # Encode query
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        with httpx.Client() as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = client.get(url, headers=headers, timeout=10)
            html = response.text
            
            # Pattern 1: JS object "videoId":"..."
            video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", html)
            if video_ids:
                # Filter out likely ad IDs or irrelevant ones if needed, but usually first is best
                logger.info(f"Found IDs (JS): {video_ids[:3]}")
                return video_ids[0]

            # Pattern 2: href="/watch?v=..."
            href_ids = re.findall(r"href=\"/watch\?v=([a-zA-Z0-9_-]{11})\"", html)
            if href_ids:
                logger.info(f"Found IDs (href): {href_ids[:3]}")
                return href_ids[0]
                
            return None
    except Exception as e:
        logger.error(f"Failed to search YouTube: {e}")
        return None

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute media-related actions.
    Actions: play_music
    """
    if action == "play_music":
        query = params.get("query", "")
        if not query:
            return {"success": False, "error": "Query required"}
        
        # 1. Search YouTube
        video_id = get_video_id(query)
        if not video_id:
            # Fallback: Just open search if we can't find ID, but user complained about this.
            # Better to error and let user know, OR try a different search method.
            return {"success": False, "error": f"Could not find any video for: {query}"}
        
        # Add autoplay
        video_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1"
        
        # 2. Open URL
        try:
            subprocess.run(["open", video_url], check=True)
            
            logger.info(f"Playing music: {query} ({video_url})")
            return {
                "success": True, 
                "message": f"Playing '{query}' on YouTube",
                "url": video_url,
                "video_id": video_id
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to open URL: {e}"}

    else:
        return {"success": False, "error": f"Unknown media action: {action}"}
