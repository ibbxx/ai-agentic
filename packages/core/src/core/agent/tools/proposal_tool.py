"""
Proposal Tool - Manages improvement proposals.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from core.agent.proposal_service import (
    list_proposals,
    approve_proposal,
    reject_proposal,
    rollback_proposal,
    format_proposals_display
)
from core.models import ProposalStatus

def execute(action: str, params: Dict[str, Any], user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute proposal-related actions.
    Actions: list, approve, reject, rollback
    """
    if action == "list":
        status_filter = params.get("status")
        if status_filter:
            status_filter = ProposalStatus(status_filter.upper())
        proposals = list_proposals(db, user_id, status_filter)
        display = format_proposals_display(proposals)
        return {"proposals": [p.id for p in proposals], "display": display, "success": True}
    
    elif action == "approve":
        proposal_id = params.get("proposal_id")
        if not proposal_id:
            return {"success": False, "error": "Proposal ID is required"}
        return approve_proposal(db, proposal_id, user_id)
    
    elif action == "reject":
        proposal_id = params.get("proposal_id")
        if not proposal_id:
            return {"success": False, "error": "Proposal ID is required"}
        return reject_proposal(db, proposal_id, user_id)
    
    elif action == "rollback":
        proposal_id = params.get("proposal_id")
        if not proposal_id:
            return {"success": False, "error": "Proposal ID is required"}
        return rollback_proposal(db, proposal_id, user_id)
    
    else:
        return {"error": f"Unknown proposal action: {action}"}
