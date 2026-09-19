# MigrateFlow Implementation Checklist

Status values are `PASS`, `FAIL`, `BLOCKED`, or `PENDING`. Every `PASS` requires a path, test, or command result.

| Level | Scope | Status | Evidence |
|---:|---|---|---|
| 0 | Repository contract and architecture | PASS | Backend `pytest` 2 passed; frontend Vitest 1 passed; production build succeeded; target schema parsed. |
| 1 | Deterministic ingestion and profiling | PASS | `pytest`: 7 passed including three-file CSV/XLSX batch, masking, malformed, empty, and invalid-extension coverage. |
| 2 | Target schema and mapping intelligence | PASS | `pytest`: 11 passed; structured proposals, component scoring, aliases, ambiguity, collisions, invalid output, and labelled fallback covered. |
| 3 | Autonomy policy and human interrupt | PASS | `pytest`: 15 passed; SQLite-checkpointed StateGraph, policy gates, durable pause/correct/resume, duplicate resolution, and audit coverage. |
| 4 | Cleaning reconciliation and validation | PASS | `pytest`: 19 passed; deterministic provenance, ambiguous dates, required failures, exact merge, conflicts, immutable originals, and two-attempt escalation covered. |
| 5 | Mock target integration | PENDING | |
| 6 | Backend APIs events and persistence | PENDING | |
| 7 | Consultant user interface | PENDING | |
| 8 | Security observability and evaluation | PENDING | |
| 9 | End to end hardening | PENDING | |
| 10 | Submission package | PENDING | |

## Level evidence

Detailed acceptance evidence is added under a heading for each completed level and must include exact commands, passed and failed counts, changed files, and residual risks.

## Level 0 Repository contract and architecture

- Status: PASS
- Commands: `python -m pytest -q`, `npm test -- --reporter=verbose`, `npm run build`, target schema parse check
- Results: backend 2 passed; frontend 1 passed; TypeScript and Vite production build passed; schema parse passed
- Evidence: `backend/app/main.py`, `backend/tests/test_health.py`, `target_schema/employee.yaml`, `docs/ARCHITECTURE.md`, `docs/AUTONOMY_POLICY.md`
- Residual risk: Docker build is deferred to the end-to-end hardening level.

## Level 1 Deterministic ingestion and profiling

- Status: PASS
- Commands: `python -m pytest -q`, `python scripts/generate_sample_xlsx.py`
- Results: 7 passed; all three sample sources ingested together; CSV and XLSX profiles persisted and reloaded
- Evidence: `backend/app/ingestion/profiler.py`, `backend/app/api/batches.py`, `backend/tests/test_ingestion.py`, `sample_data/`
- Residual risk: encoding detection intentionally uses a bounded deterministic fallback list rather than probabilistic detection.

## Level 2 Target schema and mapping intelligence

- Status: PASS
- Commands: `python -m pytest -q`
- Results: 11 passed
- Evidence: `backend/app/mapping/schema.py`, `backend/app/mapping/engine.py`, `backend/app/api/mappings.py`, `backend/tests/test_mapping.py`
- Residual risk: a live Ollama call requires the configured local model and is intentionally unavailable in automated tests; deterministic fallback is explicit.

## Level 3 Autonomy policy and human interrupt

- Status: PASS
- Commands: `python -m pytest -q`
- Results: 15 passed
- Evidence: `backend/app/agent/graph.py`, `backend/app/agent/policy.py`, `backend/app/agent/service.py`, `backend/tests/test_policy.py`, `backend/tests/test_workflow.py`
- Residual risk: the HTTP workflow service mirrors durable graph state in application tables so it can be queried efficiently; the graph checkpointer remains the orchestration checkpoint contract.

## Level 4 Cleaning reconciliation and validation

- Status: PASS
- Commands: `python -m pytest -q`
- Results: 19 passed
- Evidence: `backend/app/cleaning/service.py`, `backend/app/validation/employee.py`, `backend/app/api/records.py`, `backend/tests/test_cleaning.py`
- Residual risk: probable duplicate scoring is intentionally conservative and routes any conflicting nonempty values to review.
