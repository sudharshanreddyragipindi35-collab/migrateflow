# MigrateFlow

MigrateFlow is a supervised employee-data migration workspace. It combines deterministic ingestion, mapping evidence, validation, and target integration with narrowly scoped AI assistance and explicit human review.

## Project status

Implementation is organized into independently validated levels. Evidence is tracked in `docs/IMPLEMENTATION_CHECKLIST.md`.

## Repository layout

- `backend/` - FastAPI application, orchestration, persistence, and tests
- `frontend/` - React, Vite, and TypeScript consultant interface
- `sample_data/` - safe demonstration inputs
- `target_schema/` - canonical employee target contract
- `docs/` - architecture, policy, validation, and operating notes
- `scripts/` - setup, test, and demonstration helpers

## Quick start

Detailed setup, Docker, model, test, and demo instructions are completed with the submission package.

## Architecture

The application keeps deterministic parsing, scoring, policy, validation, retries, and rollback separate from semantic model suggestions. SQLite stores durable workflow state and append-only audit evidence. See `docs/ARCHITECTURE.md` and `docs/AUTONOMY_POLICY.md`.

## Security

Do not commit `.env`, databases, uploads, raw client data, or secrets. Model inputs use masked samples and bounded profile context.

## Skills used

- Document analysis for extracting and validating the implementation brief
- Backend engineering with FastAPI, Pydantic, SQLAlchemy, and LangGraph contracts
- Frontend engineering with React, Vite, TypeScript, and accessible interaction design
- Test engineering for unit, contract, integration, and end-to-end validation
- Secure data handling for PII masking, idempotency, audit trails, and rollback controls

