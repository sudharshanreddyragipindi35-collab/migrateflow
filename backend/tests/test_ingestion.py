from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ingestion.profiler import IngestionError, profile_file
from app.main import app


def test_csv_profile_masks_pii(tmp_path: Path) -> None:
    source = tmp_path / "employees.csv"
    source.write_text("Emp ID,Email,Start Date\nE001,alice@example.com,2025-01-02\nE002,bob@example.com,2025-02-03\n")
    profile = profile_file(source, source.name)
    assert profile.row_count == 2
    email = next(item for item in profile.columns if item.name == "Email")
    assert email.inferred_type == "email"
    assert email.masked_samples == ["a***@example.com", "b***@example.com"]
    assert "alice@example.com" not in profile.model_dump_json()


def test_malformed_csv_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text('id,name\n1,"broken\n2,ok,extra\n')
    with pytest.raises(IngestionError):
        profile_file(source, source.name)


def test_batch_api_rejects_empty_and_invalid_files() -> None:
    client = TestClient(app)
    empty = client.post("/api/batches", files=[("files", ("empty.csv", b"", "text/csv"))])
    assert empty.status_code == 422
    invalid = client.post("/api/batches", files=[("files", ("data.txt", b"x", "text/plain"))])
    assert invalid.status_code == 422


def test_batch_api_persists_profile() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/batches",
        files=[("files", ("employees.csv", b"employee_id,email\n1,a@example.com\n", "text/csv"))],
    )
    assert response.status_code == 201
    batch_id = response.json()["batch_id"]
    loaded = client.get(f"/api/batches/{batch_id}/profiles")
    assert loaded.status_code == 200
    assert loaded.json()["profiles"][0]["row_count"] == 1


def test_three_sample_files_ingest_together() -> None:
    client = TestClient(app)
    root = Path(__file__).resolve().parents[2] / "sample_data"
    names = ["employees_india.csv", "employee_master.xlsx", "new_joiners.csv"]
    uploads = []
    for name in names:
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if name.endswith("xlsx") else "text/csv"
        uploads.append(("files", (name, (root / name).read_bytes(), mime)))
    response = client.post("/api/batches", files=uploads)
    assert response.status_code == 201
    profiles = response.json()["profiles"]
    assert {item["file_name"] for item in profiles} == set(names)
    assert next(item for item in profiles if item["file_name"].endswith("xlsx"))["sheet_name"] == "Employee Master"
