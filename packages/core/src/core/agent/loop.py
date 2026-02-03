"""
Agent Loop - Main orchestration function.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.agent.intent import classify_intent
from core.agent.planner import make_plan
from core.agent.executor import execute_plan
from core.agent.verifier import verify_result
from core.agent.formatter import format_reply
from core.agent.persistence import persist_run
from core.db import crud
import logging

logger = logging.getLogger(__name__)

def run_agent_loop(text: str, user_id: int, db: Session) -> Dict[str, Any]:
    """
    Main agent loop:
    1. Classify intent
    2. Make plan
    3. Execute plan
    4. Verify result
    5. Format reply
    6. Persist run
    
    Returns {response: str, run_id: int}
    """
    logger.info(f"[Agent] Starting loop for user {user_id}: {text}")
    
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
    
    return {
        "response": response,
        "run_id": run_id
    }
