"""
Agent Loop - Main orchestration function with reflection and proposal generation.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.agent.intent import classify_intent
from core.agent.planner import make_plan
from core.agent.executor import execute_plan
from core.agent.verifier import verify_result
from core.agent.formatter import format_reply
from core.agent.persistence import persist_run
from core.agent.memory_service import add_reflection
from core.agent.proposal_service import create_proposal, apply_alias_rules
from core.parser import Intent, ParsedIntent
from core.db import crud
import logging

logger = logging.getLogger(__name__)

def run_agent_loop(text: str, user_id: int, db: Session) -> Dict[str, Any]:
    """Main agent loop with reflection and proposal generation."""
    logger.info(f"[Agent] Starting loop for user {user_id}: {text}")
    
    # 0. Check active alias rules first
    alias_action = apply_alias_rules(db, user_id, text)
    if alias_action:
        logger.info(f"[Agent] Alias rule matched: {alias_action}")
        # Override intent from rule
        intent_override = alias_action.get("intent")
        if intent_override:
            parsed = ParsedIntent(intent=Intent(intent_override), params=alias_action.get("params", {}))
        else:
            parsed = classify_intent(text)
    else:
        # 1. Classify intent
        parsed = classify_intent(text)
    
    intent_str = parsed.intent.value
    logger.info(f"[Agent] Intent: {intent_str}, Params: {parsed.params}")
    
    # 2. Make plan
    plan = make_plan(parsed)
    logger.info(f"[Agent] Plan: {plan}")
    
    # 3. Execute plan
    result = execute_plan(plan, user_id, db)
    logger.info(f"[Agent] Result: {result}")
    
    # 4. Verify result
    verify = verify_result(parsed, result)
    logger.info(f"[Agent] Verify: {verify}")
    
    # 5. Format reply
    response = format_reply(parsed, result, verify)
    logger.info(f"[Agent] Response: {response}")
    
    # 6. Persist run
    status = "completed" if verify.get("ok") else "failed"
    run_id = persist_run(db, user_id, text, intent_str, plan, result, status)
    logger.info(f"[Agent] Run persisted: #{run_id}")
    
    # 7. Add reflection
    reflection = generate_reflection(parsed, result, verify)
    add_reflection(db, user_id, run_id, reflection)
    
    # 8. Generate improvement proposal if actionable suggestion exists
    if reflection.get("suggestion") and is_actionable_suggestion(reflection.get("suggestion")):
        proposal = generate_proposal_from_reflection(text, parsed, reflection)
        if proposal:
            create_proposal(db, user_id, proposal, source_run_id=run_id)
            logger.info(f"[Agent] Created improvement proposal from reflection")
    
    return {"response": response, "run_id": run_id}

def generate_reflection(parsed, result, verify) -> Dict[str, Any]:
    """Generate reflection based on run outcome."""
    what_worked = []
    what_failed = []
    suggestion = None
    
    if verify.get("ok"):
        what_worked.append(f"Successfully executed {parsed.intent.value}")
        if result.get("results"):
            for r in result["results"]:
                if r.get("result", {}).get("success"):
                    what_worked.append(f"{r['tool']}.{r['action']} succeeded")
    else:
        what_failed.extend(verify.get("issues", []))
    
    if result.get("needs_approval"):
        what_failed.append("Action required approval")
        suggestion = "User should review and approve pending actions"
    
    if parsed.intent.value == "unknown":
        what_failed.append("Could not understand user intent")
        suggestion = f"Consider adding alias rule for similar phrases"
    
    return {"what_worked": what_worked, "what_failed": what_failed, "suggestion": suggestion}

def is_actionable_suggestion(suggestion: str) -> bool:
    """Check if a suggestion is actionable (can become a rule)."""
    if not suggestion:
        return False
    actionable_keywords = ["alias", "rule", "add", "consider", "similar", "pattern"]
    return any(kw in suggestion.lower() for kw in actionable_keywords)

def generate_proposal_from_reflection(original_text: str, parsed, reflection: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a proposal from an actionable reflection."""
    if parsed.intent.value == "unknown":
        # Suggest creating an alias for the unknown phrase
        return {
            "rule_type": "alias",
            "pattern": original_text.strip().lower(),
            "action": {"intent": "unknown", "params": {}},  # User will need to set correct intent
            "description": f"Create alias for: '{original_text[:50]}...'",
            "priority": 0
        }
    return None
