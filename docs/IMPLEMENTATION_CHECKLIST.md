# MigrateFlow Implementation Checklist

Status values are `PASS`, `FAIL`, `BLOCKED`, or `PENDING`. Every `PASS` requires a path, test, or command result.

| Level | Scope | Status | Evidence |
|---:|---|---|---|
| 0 | Repository contract and architecture | PASS | Backend `pytest` 2 passed; frontend Vitest 1 passed; production build succeeded; target schema parsed. |
| 1 | Deterministic ingestion and profiling | PENDING | |
| 2 | Target schema and mapping intelligence | PENDING | |
| 3 | Autonomy policy and human interrupt | PENDING | |
| 4 | Cleaning reconciliation and validation | PENDING | |
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
