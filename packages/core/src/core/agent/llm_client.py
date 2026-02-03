"""
LLM Client - OpenAI integration with structured output and caching.
"""
from openai import OpenAI
from core.config import get_settings
from core.agent.llm_schemas import LLMResponse, LLMIntent, ALLOWED_TOOLS, BLOCKED_PATTERNS
import json
import hashlib
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)
settings = get_settings()

# Simple in-memory cache
_cache: dict = {}
CACHE_MAX_SIZE = 100

SYSTEM_PROMPT = """You are an AI assistant that parses user messages into structured intents for a task management bot.

IMPORTANT RULES:
1. Only use these tools: task_tool, scheduler_tool, approval_tool
2. NEVER generate shell commands, system calls, or any code execution
3. NEVER output URLs, file paths, or external links
4. Keep responses focused on task management only

Available intents:
- add_task: Create a new task (needs: title)
- list_tasks: List open tasks
- done_task: Mark task complete (needs: task_id as integer)
- delete_task: Delete task permanently (needs: task_id as integer)
- daily_brief: Get daily summary
- approve: Approve a pending request (needs: approval_id as integer)
- unknown: Cannot determine intent

Available tools and actions:
- task_tool: create, list, close, delete
- scheduler_tool: daily_brief
- approval_tool: approve, reject

Respond ONLY with valid JSON matching this schema:
{
  "intent": "add_task|list_tasks|done_task|delete_task|daily_brief|approve|unknown",
  "entities": {"task_id": 123, "title": "example", "approval_id": 456},
  "plan_steps": [{"tool": "task_tool", "action": "create", "params": {"title": "example"}}],
  "confidence": 0.95
}
"""

def get_cache_key(text: str) -> str:
    """Generate cache key for text."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def get_cached_response(text: str) -> Optional[LLMResponse]:
    """Get cached LLM response if available."""
    key = get_cache_key(text)
    if key in _cache:
        logger.debug(f"[LLM] Cache hit for: {text[:30]}...")
        return _cache[key]
    return None

def cache_response(text: str, response: LLMResponse):
    """Cache LLM response."""
    if len(_cache) >= CACHE_MAX_SIZE:
        # Remove oldest entry (simple FIFO)
        oldest_key = next(iter(_cache))
        del _cache[oldest_key]
    key = get_cache_key(text)
    _cache[key] = response

def call_llm(text: str) -> Optional[LLMResponse]:
    """
    Call OpenAI to parse user message into structured intent.
    Returns None if API key not configured or on error.
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("[LLM] OPENAI_API_KEY not configured, skipping LLM fallback")
        return None
    
    # Check cache first
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
        
        # Parse and validate with Pydantic
        data = json.loads(content)
        llm_response = LLMResponse(**data)
        
        # Validate for blocked patterns in raw response
        content_lower = content.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern in content_lower:
                logger.warning(f"[LLM] Blocked pattern detected: {pattern}")
                return None
        
        # Cache successful response
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
    """Clear LLM response cache."""
    _cache.clear()
    logger.info("[LLM] Cache cleared")
