# MigrateFlow

MigrateFlow is a supervised employee-data migration workspace. It combines deterministic ingestion, mapping evidence, validation, and target integration with narrowly scoped AI assistance and explicit human review.

## What it does

MigrateFlow ingests CSV and XLSX employee exports, profiles them without exposing raw PII to a model, proposes explainable target mappings, pauses on genuine ambiguity, resumes after a reviewer decision, cleans and validates records, and writes approved records to an idempotent mock target. Retry, rollback, SSE progress, and append-only audit evidence are built into the workflow.

## Repository layout

- `backend/` - FastAPI application, orchestration, persistence, and tests
- `frontend/` - React, Vite, and TypeScript consultant interface
- `sample_data/` - safe demonstration inputs
- `target_schema/` - canonical employee target contract
- `docs/` - architecture, policy, validation, and operating notes
- `scripts/` - setup, test, and demonstration helpers

## Prerequisites

- Docker Desktop with Compose, or Python 3.12 plus Node.js 22
- Ollama for live semantic proposals; deterministic fallback is available without it
- PowerShell 7 for the included convenience scripts

## Quick start with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open the consultant UI at `http://localhost:5173`, the API at `http://localhost:8000`, and interactive OpenAPI documentation at `http://localhost:8000/docs`.

## Local development

```powershell
./scripts/setup.ps1
```

Start the backend and frontend in separate terminals:

```powershell
Set-Location backend
uvicorn app.main:app --reload
```

```powershell
Set-Location frontend
npm run dev
```

Run every quality gate:

```powershell
./scripts/test.ps1
```

## Ollama model setup

MigrateFlow uses the open-source `qwen2.5:7b-instruct` model by default.

```powershell
ollama pull qwen2.5:7b-instruct
ollama serve
```

Set `MODEL_MODE=ollama` for live structured proposals. Set `MODEL_MODE=fallback` to use the clearly labelled deterministic mapping fallback. If Ollama is selected but unavailable, the API returns an explicit 503 instead of imitating model output.

## Environment variables

Copy `.env.example` to `.env`. Important settings include:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Durable SQLite location | `sqlite:///./migrateflow.db` |
| `UPLOAD_ROOT` | Private batch upload directory | `./uploads` |
| `MAX_UPLOAD_FILES` | Per-batch file limit | `10` |
| `MAX_UPLOAD_BYTES` | Per-file byte limit | `10485760` |
| `OLLAMA_BASE_URL` | Local Ollama endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Open-source instruction model | `qwen2.5:7b-instruct` |
| `MODEL_MODE` | `ollama` or explicit `fallback` | `ollama` |
| `DEMO_FAILURES` | Enable deterministic retry demo | `false` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |

## Demo

1. Run `python scripts/demo_seed.py` to verify the three safe sample inputs.
2. Upload all files from `sample_data/` except `malformed.csv`.
3. Generate proposals in fallback mode if Ollama is not running.
4. Start the workflow. Review the single ambiguous `start_date` decision and approve or correct it.
5. Transform and inspect records, push valid rows, retry the deliberate demo failure, and review the audit export.
6. Roll back the batch and confirm unrelated target rows remain.

The timed narration and screen sequence are in `DEMO_SCRIPT.md`.

## Tests

```powershell
Set-Location backend
python -m ruff check app tests
python -m mypy app
python -m pytest -q

Set-Location ../frontend
npm run lint
npm test
npm run build

Set-Location ..
python scripts/evaluate.py
docker compose build
```

## Architecture

The application keeps deterministic parsing, scoring, policy, validation, retries, and rollback separate from semantic model suggestions. SQLite stores durable workflow state and append-only audit evidence. See `docs/ARCHITECTURE.md` and `docs/AUTONOMY_POLICY.md`.

## Security

Do not commit `.env`, databases, uploads, raw client data, or secrets. Model inputs use masked samples and bounded profile context.

## Screenshots

- New Migration: capture the three-file selection and target schema panel.
- Live Run: capture the clearly paused state.
- Review Queue: capture confidence evidence and correction controls.
- Data Preview: capture original, transformed, provenance, and validation status.
- Integration Audit: capture retry, rollback, and per-record results.

## Troubleshooting

- `503` from mapping proposals: start Ollama or use `?fallback=true` / `MODEL_MODE=fallback`.
- Frontend cannot reach the API: confirm `VITE_API_BASE_URL` and `CORS_ORIGINS` agree.
- Docker backend is unhealthy: inspect `docker compose logs backend` and confirm the data volume is writable.
- Upload rejected: use only nonempty `.csv` or `.xlsx` files within configured count and size limits.
- A record does not push: resolve all mapping decisions and inspect validation errors in Data Preview.

## Known limitations

- The evaluation corpus is intentionally small and demonstrates mechanics rather than production accuracy.
- SQLite and the prototype migration initializer suit a take-home deployment, not horizontally scaled workers.
- The mock target demonstrates integration semantics; a real connector needs client-specific authentication and rate-limit handling.
- Live semantic quality depends on the locally installed Ollama model. Deterministic safeguards do not depend on model availability.

## Skills used

- Document analysis for extracting and validating the implementation brief
- Backend engineering with FastAPI, Pydantic, SQLAlchemy, and LangGraph contracts
- Frontend engineering with React, Vite, TypeScript, and accessible interaction design
- Test engineering for unit, contract, integration, and end-to-end validation
- Secure data handling for PII masking, idempotency, audit trails, and rollback controls
