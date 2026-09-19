import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cleaning.models import RecordPreview
from app.cleaning.service import clean_record
from app.db.database import get_db
from app.db.tables import SourceFileProfileRow, TransformedRecordRow, WorkflowStateRow
from app.ingestion.profiler import read_source

router = APIRouter(prefix="/api/batches", tags=["records"])


@router.post("/{batch_id}/records/transform", response_model=list[RecordPreview])
def transform(batch_id: str, db: Session = Depends(get_db)) -> list[RecordPreview]:
    workflow = db.get(WorkflowStateRow, batch_id)
    if workflow is None or workflow.status != "COMPLETED":
        raise HTTPException(409, "Resolve mapping review before transforming records")
    applied = json.loads(workflow.state_json).get("applied_mappings", {})
    rows = db.scalars(select(SourceFileProfileRow).where(SourceFileProfileRow.batch_id == batch_id)).all()
    previews: list[RecordPreview] = []
    for source in rows:
        frame, _, _ = read_source(__import__("pathlib").Path(source.storage_path))
        mapping = {
            key.split(":", 1)[1]: target for key, target in applied.items() if key.startswith(f"{source.safe_name}:")
        }
        for number, record in enumerate(frame.to_dict(orient="records"), start=1):
            preview = clean_record(source.safe_name, str(number), record, mapping)
            previews.append(preview)
            db.merge(
                TransformedRecordRow(
                    id=preview.record_id, batch_id=batch_id, source_file=source.safe_name,
                    source_record_id=preview.source_record_id,
                    original_json=json.dumps(preview.original, default=str),
                    transformed_json=json.dumps(preview.transformed, default=str),
                    provenance_json=json.dumps([item.model_dump(mode="json") for item in preview.provenance], default=str),
                    status=preview.status, errors_json=json.dumps(preview.errors), attempt_count=preview.attempt_count,
                )
            )
    db.commit()
    return previews


@router.get("/{batch_id}/records", response_model=list[RecordPreview])
def previews(batch_id: str, db: Session = Depends(get_db)) -> list[RecordPreview]:
    rows = db.scalars(select(TransformedRecordRow).where(TransformedRecordRow.batch_id == batch_id)).all()
    return [
        RecordPreview(
            record_id=row.id, source_file=row.source_file, source_record_id=row.source_record_id,
            original=json.loads(row.original_json), transformed=json.loads(row.transformed_json),
            provenance=json.loads(row.provenance_json), status=row.status,
            errors=json.loads(row.errors_json), attempt_count=row.attempt_count,
        )
        for row in rows
    ]

