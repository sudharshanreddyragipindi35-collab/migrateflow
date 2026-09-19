import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.models import Escalation, EscalationAction, EscalationDecision, WorkflowStatus
from app.agent.policy import evaluate_mapping
from app.db.tables import AuditEventRow, EscalationRow, MappingProposalRow, WorkflowStateRow
from app.mapping.models import MappingProposal
from app.mapping.schema import load_target_schema


def _audit(db: Session, batch_id: str, actor_type: str, actor_id: str, action: str, entity_type: str, entity_id: str, details: dict) -> None:
    db.add(
        AuditEventRow(
            batch_id=batch_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=json.dumps(details, separators=(",", ":")),
        )
    )


def _status(row: WorkflowStateRow, open_count: int) -> WorkflowStatus:
    state = json.loads(row.state_json)
    return WorkflowStatus(
        batch_id=row.batch_id,
        thread_id=row.thread_id,
        status=row.status,
        applied_mappings=state.get("applied_mappings", {}),
        open_escalations=open_count,
    )


def start_workflow(db: Session, batch_id: str) -> WorkflowStatus:
    existing = db.get(WorkflowStateRow, batch_id)
    if existing is not None and existing.status in {"RUNNING", "PAUSED", "COMPLETED"}:
        count = len(db.scalars(select(EscalationRow).where(EscalationRow.batch_id == batch_id, EscalationRow.status == "OPEN")).all())
        return _status(existing, count)
    rows = db.scalars(select(MappingProposalRow).where(MappingProposalRow.batch_id == batch_id)).all()
    if not rows:
        raise HTTPException(409, "Generate mapping proposals before starting the workflow")
    applied: dict[str, str] = {}
    open_count = 0
    for row in rows:
        proposal = MappingProposal.model_validate_json(row.proposal_json)
        decision = evaluate_mapping(proposal)
        key = f"{proposal.source_file}:{proposal.source_column}"
        if decision.auto_apply and proposal.target_field:
            applied[key] = proposal.target_field
            _audit(db, batch_id, "AGENT", "policy", "mapping.auto_applied", "mapping", key, {"target": proposal.target_field, "confidence": proposal.confidence})
            continue
        escalation_id = str(uuid4())
        db.add(
            EscalationRow(
                id=escalation_id,
                batch_id=batch_id,
                source_context_json=json.dumps({"source_file": proposal.source_file, "source_column": proposal.source_column}),
                suggestion=proposal.target_field,
                alternatives_json=json.dumps(proposal.alternatives),
                confidence_json=proposal.evidence.model_dump_json(),
                reason_code=decision.reason_code,
                allowed_actions_json=json.dumps([item.value for item in EscalationAction]),
            )
        )
        _audit(db, batch_id, "AGENT", "policy", "escalation.created", "escalation", escalation_id, {"reason_code": decision.reason_code})
        open_count += 1
    status = "PAUSED" if open_count else "COMPLETED"
    state = {"applied_mappings": applied, "resume_count": 0}
    workflow = WorkflowStateRow(batch_id=batch_id, thread_id=batch_id, status=status, state_json=json.dumps(state))
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return _status(workflow, open_count)


def escalation_model(row: EscalationRow) -> Escalation:
    return Escalation(
        escalation_id=row.id,
        batch_id=row.batch_id,
        source_context=json.loads(row.source_context_json),
        suggestion=row.suggestion,
        alternatives=json.loads(row.alternatives_json),
        confidence_evidence=json.loads(row.confidence_json),
        reason_code=row.reason_code,
        allowed_actions=json.loads(row.allowed_actions_json),
        status=row.status,
        decision=json.loads(row.decision_json) if row.decision_json else None,
        actor=row.actor,
        created_at=row.created_at,
        resolved_at=row.resolved_at,
    )


def resolve_escalation(db: Session, row: EscalationRow, decision: EscalationDecision) -> WorkflowStatus:
    if row.status != "OPEN":
        raise HTTPException(409, "Escalation has already been resolved")
    target_fields = {item.name for item in load_target_schema().fields}
    selected = row.suggestion
    if decision.action == EscalationAction.CORRECT:
        selected = decision.corrected_value
        if selected not in target_fields:
            raise HTTPException(422, "Correction must be a target schema field")
    row.status = "RESOLVED"
    row.decision_json = decision.model_dump_json()
    row.actor = decision.actor
    row.resolved_at = datetime.now(timezone.utc)
    workflow = db.get(WorkflowStateRow, row.batch_id)
    if workflow is None:
        raise HTTPException(409, "Workflow state is missing")
    state = json.loads(workflow.state_json)
    key = f"{json.loads(row.source_context_json)['source_file']}:{json.loads(row.source_context_json)['source_column']}"
    if decision.action in {EscalationAction.APPROVE, EscalationAction.CORRECT} and selected:
        state.setdefault("applied_mappings", {})[key] = selected
    else:
        state.setdefault("rejected_mappings", {})[key] = row.reason_code
    state["resume_count"] = state.get("resume_count", 0) + 1
    workflow.state_json = json.dumps(state)
    remaining = len(
        db.scalars(
            select(EscalationRow).where(
                EscalationRow.batch_id == row.batch_id,
                EscalationRow.status == "OPEN",
                EscalationRow.id != row.id,
            )
        ).all()
    )
    workflow.status = "PAUSED" if remaining else "COMPLETED"
    _audit(
        db, row.batch_id, "HUMAN", decision.actor, "escalation.resolved", "escalation", row.id,
        {"action": decision.action.value, "selected": selected},
    )
    db.commit()
    db.refresh(workflow)
    return _status(workflow, remaining)

