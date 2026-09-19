import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_db
from app.db.tables import TargetWriteRow, TransformedRecordRow
from app.integration.models import PushRequest, PushResult
from app.integration.service import payload_hash, push_record, retry_batch, rollback_batch
from app.events.service import emit_event

router = APIRouter(prefix="/mock-target", tags=["mock-target"])


@router.post("/migrations/{batch_id}/push-valid", response_model=list[PushResult])
def push_valid(batch_id: str, db: Session = Depends(get_db)) -> list[PushResult]:
    rows = db.scalars(
        select(TransformedRecordRow).where(
            TransformedRecordRow.batch_id == batch_id,
            TransformedRecordRow.status == "VALID",
        )
    ).all()
    results: list[PushResult] = []
    for row in rows:
        result = push_record(
            db,
            PushRequest(
                batch_id=batch_id,
                record_id=row.id,
                source_record_id=row.source_record_id,
                idempotency_key=f"{batch_id}:{row.source_file}:{row.source_record_id}",
                payload_hash=payload_hash(json.loads(row.transformed_json)),
            ),
            demo_failures=get_settings().demo_failures,
        )
        emit_event(
            db,
            batch_id,
            "push_result",
            {"source_record_id": result.source_record_id, "status": result.status.value},
        )
        results.append(result)
    db.commit()
    return results


@router.post("/employees", response_model=PushResult)
def push(request: PushRequest, db: Session = Depends(get_db)) -> PushResult:
    result = push_record(db, request, demo_failures=get_settings().demo_failures)
    emit_event(db, request.batch_id, "push_result", {"source_record_id": result.source_record_id, "status": result.status.value})
    db.commit()
    return result


@router.get("/migrations/{batch_id}", response_model=list[PushResult])
def migration(batch_id: str, db: Session = Depends(get_db)) -> list[PushResult]:
    rows = db.scalars(select(TargetWriteRow).where(TargetWriteRow.batch_id == batch_id)).all()
    return [
        PushResult(
            target_write_id=row.id, batch_id=row.batch_id, source_record_id=row.source_record_id,
            idempotency_key=row.idempotency_key, payload_hash=row.payload_hash,
            status=row.status, retry_count=row.retry_count,
        )
        for row in rows
    ]


@router.post("/migrations/{batch_id}/retry", response_model=list[PushResult])
def retry(batch_id: str, db: Session = Depends(get_db)) -> list[PushResult]:
    results = retry_batch(db, batch_id)
    for item in results:
        emit_event(db, batch_id, "push_result", {"source_record_id": item.source_record_id, "status": item.status.value, "retry_count": item.retry_count})
    db.commit()
    return results


@router.delete("/migrations/{batch_id}")
def rollback(batch_id: str, db: Session = Depends(get_db)) -> dict[str, int | str]:
    count = rollback_batch(db, batch_id)
    emit_event(db, batch_id, "rollback", {"rolled_back": count})
    db.commit()
    return {"batch_id": batch_id, "rolled_back": count}
