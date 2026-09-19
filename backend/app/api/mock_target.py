from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_db
from app.db.tables import TargetWriteRow
from app.integration.models import PushRequest, PushResult
from app.integration.service import push_record, retry_batch, rollback_batch

router = APIRouter(prefix="/mock-target", tags=["mock-target"])


@router.post("/employees", response_model=PushResult)
def push(request: PushRequest, db: Session = Depends(get_db)) -> PushResult:
    return push_record(db, request, demo_failures=get_settings().demo_failures)


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
    return retry_batch(db, batch_id)


@router.delete("/migrations/{batch_id}")
def rollback(batch_id: str, db: Session = Depends(get_db)) -> dict[str, int | str]:
    return {"batch_id": batch_id, "rolled_back": rollback_batch(db, batch_id)}

