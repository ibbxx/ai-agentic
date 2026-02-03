"""
LLM Client - OpenAI integration with structured output for computer use.
"""
from openai import OpenAI
from core.config import get_settings
from core.agent.llm_schemas import LLMResponse, LLMIntent, ALLOWED_TOOLS, BLOCKED_PATTERNS
import json
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)
settings = get_settings()

# Simple in-memory cache
_cache: dict = {}
CACHE_MAX_SIZE = 100

SYSTEM_PROMPT = """You are an AI assistant that can control a macOS laptop. Parse user messages into structured actions.

AVAILABLE TOOLS:
- task_tool: create/list/close/delete tasks
- scheduler_tool: daily_brief
- approval_tool: approve pending requests
- preference_tool: get/set user preferences
- shell_tool: run terminal commands (run, pwd, ls)
- file_tool: read/write/list/delete files
- app_tool: open/close/list/focus applications

AVAILABLE INTENTS:
- add_task, list_tasks, done_task, delete_task, daily_brief, approve
- run_command: Execute terminal command
- read_file: Read file contents
- write_file: Write to a file
- list_files: List directory contents
- open_app: Open an application
- close_app: Close an application
- screenshot: Take a screenshot
- unknown: Cannot determine intent

EXAMPLES:
User: "buka chrome" → {intent: "open_app", plan_steps: [{tool: "app_tool", action: "open", params: {app: "Chrome"}}]}
User: "jalankan ls -la" → {intent: "run_command", plan_steps: [{tool: "shell_tool", action: "run", params: {command: "ls -la"}}]}
User: "baca file ~/readme.md" → {intent: "read_file", plan_steps: [{tool: "file_tool", action: "read", params: {path: "~/readme.md"}}]}
User: "tutup spotify" → {intent: "close_app", plan_steps: [{tool: "app_tool", action: "close", params: {app: "Spotify"}}]}
User: "buka cursor dan file /path/to/file.py" → {intent: "open_app", plan_steps: [{tool: "app_tool", action: "open", params: {app: "Cursor", file: "/path/to/file.py"}}]}

RULES:
1. Only use listed tools
2. Never generate dangerous commands (rm -rf /, sudo rm, etc)
3. Be precise with file paths and app names

Respond ONLY with valid JSON:
{
  "intent": "...",
  "entities": {...},
  "plan_steps": [{tool, action, params}, ...],
  "confidence": 0.95
}
"""

def get_cache_key(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def get_cached_response(text: str) -> Optional[LLMResponse]:
    key = get_cache_key(text)
    if key in _cache:
        logger.debug(f"[LLM] Cache hit for: {text[:30]}...")
        return _cache[key]
    return None

def cache_response(text: str, response: LLMResponse):
    if len(_cache) >= CACHE_MAX_SIZE:
        oldest_key = next(iter(_cache))
        del _cache[oldest_key]
    key = get_cache_key(text)
    _cache[key] = response

def call_llm(text: str) -> Optional[LLMResponse]:
    """Call OpenAI to parse user message into structured intent."""
    if not settings.OPENAI_API_KEY:
        logger.warning("[LLM] OPENAI_API_KEY not configured, skipping LLM fallback")
        return None
    
    cached = get_cached_response(text)
    if cached:
        return cached
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Parse this message: {text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        logger.info(f"[LLM] Raw response: {content}")
        
        data = json.loads(content)
        llm_response = LLMResponse(**data)
        
        content_lower = content.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern.lower() in content_lower:
                logger.warning(f"[LLM] Blocked pattern detected: {pattern}")
                return None
        
        cache_response(text, llm_response)
        logger.info(f"[LLM] Parsed intent: {llm_response.intent}, confidence: {llm_response.confidence}")
        return llm_response
        
    except json.JSONDecodeError as e:
        logger.error(f"[LLM] Invalid JSON response: {e}")
        return None
    except ValueError as e:
        logger.error(f"[LLM] Validation error: {e}")
        return None
    except Exception as e:
        logger.error(f"[LLM] API error: {e}")
        return None

def clear_cache():
    _cache.clear()
    logger.info("[LLM] Cache cleared")
