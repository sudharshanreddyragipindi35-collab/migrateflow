# MigrateFlow Architecture

## System boundary

MigrateFlow is a supervised migration system with a FastAPI backend, React consultant interface, SQLite state store, and a local Ollama model adapter. LangGraph owns workflow orchestration. It does not own policy or irreversible authority.

## Components

1. Ingestion parses bounded CSV and XLSX uploads into immutable source records and masked profiles.
2. Mapping combines deterministic evidence with optional structured model proposals.
3. The autonomy policy decides whether a proposal is safe to apply or must pause for a person.
4. Cleaning and validation produce canonical records with field-level provenance.
5. Integration writes approved records with idempotency keys and batch-scoped compensation.
6. Audit storage records material actions as append-only events.

## Ownership decisions

- Deterministic policy controls autonomy.
- LangGraph owns orchestration and durable pause and resume.
- SQLite owns durable application state.
- Audit entries are append only.
- Ollama is the default model path.
- Mock mode is explicit and may not imitate model intelligence.

## Data flow

Uploaded files are stored outside public paths under generated batch identifiers. Only bounded column metadata, aggregate statistics, and masked examples may reach a model. Raw records remain in deterministic processing paths. Target writes occur only after mapping, validation, and approval gates pass.

