"""
Intent Classification - Determines what the user wants to do.
"""
from core.parser import parse_message, Intent, ParsedIntent

def classify_intent(text: str) -> ParsedIntent:
    """
    Classify user message into an intent with parameters.
    Currently uses rule-based parser; can be swapped for LLM later.
    """
    return parse_message(text)
