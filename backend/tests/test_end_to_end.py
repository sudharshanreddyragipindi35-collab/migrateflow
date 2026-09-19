from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from app.db.database import SessionLocal
from app.db.tables import TransformedRecordRow
from app.integration.models import PushRequest, PushStatus
from app.integration.service import payload_hash, push_record, retry_batch, rollback_batch
from app.main import app

def test_complete_supervised_scenario_with_retry_and_rollback() -> None:
    client=TestClient(app); root=Path(__file__).resolve().parents[2]/"sample_data"; names=["employees_india.csv","employee_master.xlsx","new_joiners.csv"]
    uploads=[]
    for name in names: uploads.append(("files",(name,(root/name).read_bytes(),"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if name.endswith("xlsx") else "text/csv")))
    created=client.post("/api/batches",files=uploads); assert created.status_code==201; batch=created.json()["batch_id"]
    proposals=client.post(f"/api/batches/{batch}/mapping-proposals?fallback=true").json(); ambiguous=[item for item in proposals if "AMBIGUOUS_DATE" in item["warnings"]]; assert len(ambiguous)==1
    started=client.post(f"/api/batches/{batch}/workflow/start").json(); assert started["status"]=="PAUSED" and started["open_escalations"]==1
    escalation=client.get(f"/api/batches/{batch}/escalations").json()[0]; resolved=client.post(f"/api/escalations/{escalation['escalation_id']}/resolve",json={"action":"APPROVE","actor":"demo-consultant"}); assert resolved.json()["status"]=="COMPLETED"
    restarted=TestClient(app); assert restarted.get(f"/api/batches/{batch}/workflow/status").json()["status"]=="COMPLETED"
    previews=restarted.post(f"/api/batches/{batch}/records/transform").json(); valid=[item for item in previews if item["status"]=="VALID"]; assert valid
    retry_preview=next(item for item in valid if "retry." in item["transformed"].get("email",""))
    with SessionLocal() as db:
        staged=db.get(TransformedRecordRow,retry_preview["record_id"]); payload=retry_preview["transformed"]; request=PushRequest(batch_id=batch,record_id=staged.id,source_record_id=staged.source_record_id,idempotency_key=f"e2e-{uuid4()}",payload_hash=payload_hash(payload)); first=push_record(db,request,demo_failures=True); assert first.status==PushStatus.RETRYABLE_FAILURE; retried=retry_batch(db,batch); assert retried[0].status==PushStatus.SUCCESS; assert rollback_batch(db,batch)==1
