"""
Vision Tool - Screen analysis using Groq Vision API.
Uses llama-3.2-90b-vision-preview to understand screen content.
"""
import os
import base64
from typing import Dict, Any, Optional
from groq import Groq
from core.config import get_settings
from core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

SCREENSHOT_DIR = os.path.expanduser("/Users/ibnufajar/Documents/screenshoot")

def get_groq_client() -> Optional[Groq]:
    """Get Groq client."""
    if not settings.GROQ_API_KEY:
        return None
    return Groq(api_key=settings.GROQ_API_KEY)

def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def get_latest_screenshot() -> Optional[str]:
    """Get the most recent screenshot."""
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        return None
    
    files = []
    for f in os.listdir(SCREENSHOT_DIR):
        if f.endswith(('.png', '.jpg', '.jpeg')):
            full_path = os.path.join(SCREENSHOT_DIR, f)
            files.append((full_path, os.path.getmtime(full_path)))
    
    if not files:
        return None
    
    files.sort(key=lambda x: x[1], reverse=True)
    return files[0][0]

def analyze_screen(image_path: str, question: str) -> Dict[str, Any]:
    """
    Analyze a screenshot and answer a question about it.
    Can find element positions, read text, understand UI state.
    """
    client = get_groq_client()
    if not client:
        return {"success": False, "error": "Groq API key not configured"}
    
    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}
    
    try:
        base64_image = encode_image(image_path)
        
        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analisis screenshot ini dan jawab pertanyaan berikut:

{question}

Jika diminta mencari posisi elemen, berikan koordinat x,y dalam format JSON.
Jika diminta membaca teks, berikan teks yang terlihat.
Jika diminta mendeskripsikan layar, jelaskan apa yang terlihat.

Format respons sebagai JSON:
{{"answer": "...", "coordinates": {{"x": 0, "y": 0}} jika ada, "confidence": "high/medium/low"}}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        logger.info(f"Vision response: {content}")
        
        return {
            "success": True,
            "response": content,
            "image_path": image_path
        }
        
    except Exception as e:
        logger.error(f"Vision error: {e}")
        return {"success": False, "error": str(e)}

def find_element(element_description: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Find an element on screen and return its coordinates.
    If no image_path provided, uses the latest screenshot.
    """
    if not image_path:
        image_path = get_latest_screenshot()
        if not image_path:
            return {"success": False, "error": "No screenshot available"}
    
    question = f"""Cari posisi elemen berikut di layar: "{element_description}"
    
Berikan koordinat x,y tengah elemen tersebut (dalam pixel dari kiri atas layar).
Jika tidak ditemukan, katakan tidak ditemukan."""
    
    return analyze_screen(image_path, question)

def read_text_from_screen(image_path: Optional[str] = None) -> Dict[str, Any]:
    """Read all visible text from the screen."""
    if not image_path:
        image_path = get_latest_screenshot()
        if not image_path:
            return {"success": False, "error": "No screenshot available"}
    
    question = "Baca dan list semua teks yang terlihat di layar ini. Kelompokkan berdasarkan area (header, sidebar, content, dll)."
    
    return analyze_screen(image_path, question)

def describe_screen(image_path: Optional[str] = None) -> Dict[str, Any]:
    """Get a description of what's on screen."""
    if not image_path:
        image_path = get_latest_screenshot()
        if not image_path:
            return {"success": False, "error": "No screenshot available"}
    
    question = "Deskripsikan apa yang terlihat di layar ini. Aplikasi apa yang terbuka? Apa status/state saat ini?"
    
    return analyze_screen(image_path, question)

def execute(action: str, params: Dict[str, Any], user_id: int, db) -> Dict[str, Any]:
    """Execute vision-related actions."""
    
    if action == "analyze":
        image_path = params.get("image_path") or get_latest_screenshot()
        question = params.get("question", "Apa yang terlihat di layar ini?")
        return analyze_screen(image_path, question)
    
    elif action == "find_element":
        element = params.get("element", "")
        if not element:
            return {"success": False, "error": "No element description provided"}
        image_path = params.get("image_path")
        return find_element(element, image_path)
    
    elif action == "read_text":
        image_path = params.get("image_path")
        return read_text_from_screen(image_path)
    
    elif action == "describe":
        image_path = params.get("image_path")
        return describe_screen(image_path)
    
    else:
        return {"success": False, "error": f"Unknown vision action: {action}"}
