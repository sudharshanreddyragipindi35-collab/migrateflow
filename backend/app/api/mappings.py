import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_db
from app.db.tables import IngestionBatchRow, MappingProposalRow, SourceFileProfileRow
from app.ingestion.models import SourceFileProfile
from app.mapping.engine import DeterministicFallback, MappingModel, ModelUnavailable, OllamaMappingAdapter, propose_mappings
from app.mapping.models import MappingProposal
from app.mapping.schema import load_target_schema

router = APIRouter(prefix="/api/batches", tags=["mapping"])


def _profiles(db: Session, batch_id: str) -> list[SourceFileProfile]:
    rows = db.scalars(select(SourceFileProfileRow).where(SourceFileProfileRow.batch_id == batch_id)).all()
    return [SourceFileProfile.model_validate_json(row.profile_json) for row in rows]


@router.post("/{batch_id}/mapping-proposals", response_model=list[MappingProposal])
def create_mapping_proposals(
    batch_id: str, fallback: bool = Query(False), db: Session = Depends(get_db)
) -> list[MappingProposal]:
    if db.get(IngestionBatchRow, batch_id) is None:
        raise HTTPException(404, "Batch not found")
    settings = get_settings()
    adapter: MappingModel
    if fallback or settings.model_mode == "fallback":
        adapter = DeterministicFallback()
    else:
        try:
            adapter = OllamaMappingAdapter(settings.ollama_base_url, settings.ollama_model)
        except ModelUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
    proposals = propose_mappings(_profiles(db, batch_id), load_target_schema(), adapter)
    db.execute(delete(MappingProposalRow).where(MappingProposalRow.batch_id == batch_id))
    for proposal in proposals:
        db.add(
            MappingProposalRow(
                batch_id=batch_id,
                source_file=proposal.source_file,
                source_column=proposal.source_column,
                proposal_json=proposal.model_dump_json(),
            )
        )
    db.commit()
    return proposals


@router.get("/{batch_id}/mapping-proposals", response_model=list[MappingProposal])
def get_mapping_proposals(batch_id: str, db: Session = Depends(get_db)) -> list[MappingProposal]:
    rows = db.scalars(
        select(MappingProposalRow).where(MappingProposalRow.batch_id == batch_id).order_by(MappingProposalRow.id)
    ).all()
    if not rows and db.get(IngestionBatchRow, batch_id) is None:
        raise HTTPException(404, "Batch not found")
    return [MappingProposal.model_validate(json.loads(row.proposal_json)) for row in rows]
