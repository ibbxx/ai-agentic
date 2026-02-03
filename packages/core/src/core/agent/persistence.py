"""
Persistence - Logs agent runs to database.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.db import crud
from core.models import AgentRunStatus

def persist_run(
    db: Session,
    user_id: int,
    input_text: str,
    intent: str,
    plan: Dict[str, Any],
    result: Dict[str, Any],
    status: str
) -> int:
    """
    Persist agent run to agent_runs table.
    Returns the run ID.
    """
    # Determine status enum
    if status == "completed":
        run_status = AgentRunStatus.COMPLETED
    elif status == "failed":
        run_status = AgentRunStatus.FAILED
    else:
        run_status = AgentRunStatus.RUNNING
    
    # Create run
    run = crud.create_agent_run(db, user_id, input_text, intent)
    
    # Update with results
    run = crud.update_agent_run(db, run.id, run_status, result=result, plan=plan)
    
    return run.id
