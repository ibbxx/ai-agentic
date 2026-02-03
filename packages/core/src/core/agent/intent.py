"""
Intent Classification - Rule-based with LLM fallback.
"""
from core.parser import parse_message, Intent, ParsedIntent
from core.agent.llm_client import call_llm
from core.agent.llm_schemas import LLMIntent
import logging

logger = logging.getLogger(__name__)

# Map LLM intents to parser intents
LLM_TO_PARSER_INTENT = {
    LLMIntent.ADD_TASK: Intent.ADD_TASK,
    LLMIntent.LIST_TASKS: Intent.LIST_TASKS,
    LLMIntent.DONE_TASK: Intent.DONE_TASK,
    LLMIntent.DELETE_TASK: Intent.DELETE_TASK,
    LLMIntent.DAILY_BRIEF: Intent.DAILY_BRIEF,
    LLMIntent.APPROVE: Intent.APPROVE,
    LLMIntent.UNKNOWN: Intent.UNKNOWN,
}

def classify_intent(text: str) -> ParsedIntent:
    """
    Classify user message into an intent with parameters.
    Uses rule-based parser first, falls back to LLM if unknown.
    """
    # Try rule-based parsing first
    parsed = parse_message(text)
    
    if parsed.intent != Intent.UNKNOWN:
        logger.info(f"[Intent] Rule-based match: {parsed.intent}")
        return parsed
    
    # Fallback to LLM
    logger.info(f"[Intent] Rule-based failed, trying LLM fallback...")
    llm_response = call_llm(text)
    
    if llm_response and llm_response.intent != LLMIntent.UNKNOWN:
        # Convert LLM response to ParsedIntent
        intent = LLM_TO_PARSER_INTENT.get(llm_response.intent, Intent.UNKNOWN)
        params = llm_response.entities
        
        logger.info(f"[Intent] LLM match: {intent}, confidence: {llm_response.confidence}")
        return ParsedIntent(intent=intent, params=params)
    
    # Both failed
    logger.info(f"[Intent] No match found for: {text}")
    return parsed
