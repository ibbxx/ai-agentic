"""
Proposal Service - Manages improvement proposals and active rules.
"""
from sqlalchemy.orm import Session
from core.models import ImprovementProposal, ActiveRule, ProposalStatus
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

# Supported rule types
RULE_TYPES = {
    "alias": "Maps user phrase to specific intent",
    "format_override": "Changes response format for specific intent",
    "response_style": "Modifies response style (brief, detailed, emoji)",
}

def create_proposal(
    db: Session, 
    user_id: int, 
    proposal_json: Dict[str, Any], 
    source_run_id: int = None
) -> ImprovementProposal:
    """Create a new improvement proposal."""
    proposal = ImprovementProposal(
        user_id=user_id,
        proposal_json=proposal_json,
        source_run_id=source_run_id,
        status=ProposalStatus.PENDING
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    logger.info(f"[Proposal] Created #{proposal.id}: {proposal_json.get('description')}")
    return proposal

def list_proposals(db: Session, user_id: int, status: ProposalStatus = None) -> List[ImprovementProposal]:
    """List proposals for user, optionally filtered by status."""
    query = db.query(ImprovementProposal).filter(ImprovementProposal.user_id == user_id)
    if status:
        query = query.filter(ImprovementProposal.status == status)
    return query.order_by(ImprovementProposal.created_at.desc()).all()

def approve_proposal(db: Session, proposal_id: int, user_id: int) -> Dict[str, Any]:
    """Approve a proposal and create active rule."""
    proposal = db.query(ImprovementProposal).filter(
        ImprovementProposal.id == proposal_id,
        ImprovementProposal.user_id == user_id
    ).first()
    
    if not proposal:
        return {"success": False, "error": f"Proposal #{proposal_id} not found"}
    
    if proposal.status != ProposalStatus.PENDING:
        return {"success": False, "error": f"Proposal is already {proposal.status.value}"}
    
    pj = proposal.proposal_json
    
    # Create active rule
    rule = ActiveRule(
        user_id=user_id,
        proposal_id=proposal_id,
        rule_type=pj.get("rule_type", "alias"),
        pattern=pj.get("pattern", ""),
        action=pj.get("action", {}),
        priority=pj.get("priority", 0),
        is_active=True
    )
    db.add(rule)
    
    # Update proposal status
    proposal.status = ProposalStatus.APPROVED
    proposal.decided_at = datetime.utcnow()
    
    db.commit()
    logger.info(f"[Proposal] Approved #{proposal_id}, created rule #{rule.id}")
    
    return {"success": True, "proposal_id": proposal_id, "rule_id": rule.id}

def reject_proposal(db: Session, proposal_id: int, user_id: int) -> Dict[str, Any]:
    """Reject a proposal."""
    proposal = db.query(ImprovementProposal).filter(
        ImprovementProposal.id == proposal_id,
        ImprovementProposal.user_id == user_id
    ).first()
    
    if not proposal:
        return {"success": False, "error": f"Proposal #{proposal_id} not found"}
    
    proposal.status = ProposalStatus.REJECTED
    proposal.decided_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "proposal_id": proposal_id}

def rollback_proposal(db: Session, proposal_id: int, user_id: int) -> Dict[str, Any]:
    """Rollback an approved proposal (deactivate its rules)."""
    proposal = db.query(ImprovementProposal).filter(
        ImprovementProposal.id == proposal_id,
        ImprovementProposal.user_id == user_id
    ).first()
    
    if not proposal:
        return {"success": False, "error": f"Proposal #{proposal_id} not found"}
    
    if proposal.status != ProposalStatus.APPROVED:
        return {"success": False, "error": "Can only rollback approved proposals"}
    
    # Deactivate all rules from this proposal
    rules = db.query(ActiveRule).filter(
        ActiveRule.proposal_id == proposal_id,
        ActiveRule.is_active == True
    ).all()
    
    for rule in rules:
        rule.is_active = False
        rule.deactivated_at = datetime.utcnow()
    
    proposal.status = ProposalStatus.ROLLED_BACK
    db.commit()
    
    logger.info(f"[Proposal] Rolled back #{proposal_id}, deactivated {len(rules)} rules")
    return {"success": True, "proposal_id": proposal_id, "rules_deactivated": len(rules)}

def get_active_rules(db: Session, user_id: int) -> List[ActiveRule]:
    """Get all active rules for user, sorted by priority."""
    return db.query(ActiveRule).filter(
        ActiveRule.user_id == user_id,
        ActiveRule.is_active == True
    ).order_by(ActiveRule.priority.desc()).all()

def apply_alias_rules(db: Session, user_id: int, text: str) -> Optional[Dict[str, Any]]:
    """
    Check if text matches any alias rules and return the mapped intent.
    Returns None if no match.
    """
    rules = get_active_rules(db, user_id)
    normalized = text.strip().lower()
    
    for rule in rules:
        if rule.rule_type != "alias":
            continue
        
        pattern = rule.pattern.lower()
        
        # Simple contains or exact match
        if pattern.startswith("^") and pattern.endswith("$"):
            # Regex-like exact match
            if normalized == pattern[1:-1]:
                return rule.action
        elif pattern in normalized:
            return rule.action
        
        # Try regex
        try:
            if re.match(pattern, normalized, re.IGNORECASE):
                return rule.action
        except:
            pass
    
    return None

def format_proposals_display(proposals: List[ImprovementProposal]) -> str:
    """Format proposals for display."""
    if not proposals:
        return "📋 No proposals found."
    
    lines = ["📋 **Improvement Proposals**\n"]
    for p in proposals:
        pj = p.proposal_json
        status_emoji = {"PENDING": "⏳", "APPROVED": "✅", "REJECTED": "❌", "ROLLED_BACK": "↩️"}.get(p.status.value, "")
        lines.append(f"{status_emoji} **#{p.id}** - {pj.get('description', 'No description')}")
        lines.append(f"   Type: {pj.get('rule_type', 'alias')} | Pattern: `{pj.get('pattern', '')}`")
        if p.status == ProposalStatus.PENDING:
            lines.append(f"   → `approve proposal {p.id}` or `reject proposal {p.id}`")
        lines.append("")
    
    return "\n".join(lines)
