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
- Ollama or an Anthropic API key for live semantic proposals; deterministic fallback is available without either
- PowerShell 7 for the included convenience scripts

## Quick start with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open the consultant UI at `http://localhost:5173`, the API at `http://localhost:8000`, and interactive OpenAPI documentation at `http://localhost:8000/docs`.

The UI header and `GET /api/system/model` show the active provider, model name, and readiness without exposing credentials.

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

With the Docker stack running, execute the transactional runtime smoke test and a bounded read-only spike test:

```powershell
python scripts/smoke_test.py
python scripts/load_test.py --pattern spike --baseline-users 5 --users 100 --requests-per-user 5
```

Add `--live-model` to the smoke command only when you intentionally want to exercise every mapping call through the configured LLM; the default smoke path stays fast and does not consume a hosted-provider quota.

## Ollama model setup

MigrateFlow uses the open-source `qwen2.5:7b-instruct` model by default.

Use this Ollama path for the submitted Darwinbox walkthrough because the assignment explicitly asks for an open-source model. The Anthropic adapter is retained as an optional enterprise/provider-abstraction demonstration, not as the recommended submission mode.

```powershell
ollama pull qwen2.5:7b-instruct
ollama serve
```

Set `MODEL_MODE=ollama` for live structured proposals. Set `MODEL_MODE=fallback` to use the clearly labelled deterministic mapping fallback. If Ollama is selected but unavailable, the API returns an explicit 503 instead of imitating model output.

Live semantic proposals are batched once per source file rather than once per column. A local 7B model can still take one to three minutes on CPU-heavy hardware; use fallback mode for a fast UI walkthrough and Ollama mode for the final open-source-model demonstration.

## Anthropic model setup

The Anthropic adapter uses the same minimized, masked context and structured `ModelMapping` contract as Ollama. Keep the committed placeholder empty, then set these values only in your untracked `.env`:

```dotenv
MODEL_MODE=anthropic
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Put your real key after `ANTHROPIC_API_KEY=` locally. A blank key fails closed with an explicit 503 before any provider request is attempted.

## Environment variables

Copy `.env.example` to `.env`. Important settings include:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Durable local SQLite location | `sqlite:///./data/migrateflow.db` |
| `UPLOAD_ROOT` | Private batch upload directory | `./uploads` |
| `MAX_UPLOAD_FILES` | Per-batch file limit | `10` |
| `MAX_UPLOAD_BYTES` | Per-file byte limit | `10485760` |
| `OLLAMA_BASE_URL` | Local Ollama endpoint | `http://localhost:11434` |
| `OLLAMA_DOCKER_BASE_URL` | Host Ollama endpoint as seen from Docker | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | Open-source instruction model | `qwen2.5:7b-instruct` |
| `ANTHROPIC_API_KEY` | Anthropic credential; intentionally blank in source | blank |
| `ANTHROPIC_MODEL` | Anthropic model identifier | `claude-sonnet-4-6` |
| `LLM_REQUEST_TIMEOUT_SECONDS` | Per-model-call timeout | `30` |
| `LLM_MAX_RETRIES` | Provider retry ceiling | `2` |
| `MODEL_MODE` | `ollama`, `anthropic`, or explicit `fallback` | `ollama` |
| `DB_POOL_SIZE` | Persistent connections per production replica | `10` |
| `DB_MAX_OVERFLOW` | Temporary overflow connections per replica | `20` |
| `AUTO_CREATE_SCHEMA` | Local-only schema bootstrap; disable for replicas | `true` |
| `DEMO_FAILURES` | Enable deterministic retry demo | `false` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |

## Demo

1. Run `python scripts/demo_seed.py` to verify the three safe sample inputs.
2. Upload all files from `sample_data/` except `malformed.csv`.
3. Generate proposals in fallback mode if Ollama is not running.
4. Start the workflow. Review the ambiguous `start_date` mapping and approve or correct it.
5. Let the agent reconcile the overlapping `IN001` row automatically, then resolve the record-level validation cards for the ambiguous date, missing date, and typed identifier.
6. Inspect the reconciled preview, push only valid rows, retry the deliberate demo failure, and review the audit export.
7. Roll back the batch and confirm unrelated target rows remain.

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

The application keeps deterministic parsing, scoring, policy, validation, retries, and rollback separate from semantic model suggestions. SQLite is the local profile; PostgreSQL and stateless replicas are the production target.

- [Architecture overview](docs/ARCHITECTURE.md)
- [High-level design](docs/HIGH_LEVEL_DESIGN.md)
- [Low-level design](docs/LOW_LEVEL_DESIGN.md)
- [Scalability and capacity plan](docs/SCALABILITY_AND_CAPACITY.md)
- [GenAI engineering design](docs/GENAI_ENGINEERING.md)
- [FDE capability matrix](docs/FDE_CAPABILITY_MATRIX.md)
- [Autonomy policy](docs/AUTONOMY_POLICY.md)
- [Assignment acceptance validation](docs/ASSIGNMENT_VALIDATION.md)

For a single-host scale demonstration, set the required secrets outside source control and run `docker compose -f docker-compose.production.yml up --build --scale backend=4`. The Nginx edge listens on `http://localhost:8080`.

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
- Docker cannot reach Ollama: keep `OLLAMA_BASE_URL=http://localhost:11434` for native runs and `OLLAMA_DOCKER_BASE_URL=http://host.docker.internal:11434` for Compose. On Linux, Compose maps that name through the host gateway.
- Frontend cannot reach the API: confirm `VITE_API_BASE_URL` and `CORS_ORIGINS` agree.
- Docker backend is unhealthy: inspect `docker compose logs backend` and confirm the data volume is writable.
- Upload rejected: use only nonempty `.csv` or `.xlsx` files within configured count and size limits.
- A record does not push: resolve all mapping and record-level decisions in Review Queue, then inspect validation evidence in Data Preview.
- A date needs correction: enter it as `YYYY-MM-DD` (for example, `2024-01-15` means 15 January 2024). If the real date is unknown, reject the record instead of guessing.

## Known limitations

- The evaluation corpus is intentionally small and demonstrates mechanics rather than production accuracy.
- SQLite and the prototype migration initializer suit a take-home deployment, not horizontally scaled workers; the production design requires PostgreSQL and versioned migrations.
- The mock target demonstrates integration semantics; a real connector needs client-specific authentication and rate-limit handling.
- Live semantic quality depends on the selected Ollama or Anthropic model and provider quota. Deterministic safeguards do not depend on model availability.

## Skills used

- Document analysis for extracting and validating the implementation brief
- Backend engineering with FastAPI, Pydantic, SQLAlchemy, and LangGraph contracts
- Frontend engineering with React, Vite, TypeScript, and accessible interaction design
- Test engineering for unit, contract, integration, and end-to-end validation
- Secure data handling for PII masking, idempotency, audit trails, and rollback controls
- System design for HLD, LLD, load balancing, database pooling, capacity tiers, and resilience testing
- GenAI engineering for provider abstraction, structured output, prompt-injection defense, human review, and evaluation
