from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.batches import router as batches_router
from app.api.mappings import router as mappings_router
from app.api.workflow import router as workflow_router
from app.api.records import router as records_router
from app.db.database import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="MigrateFlow API", version="0.1.0")
    init_db()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[item.strip() for item in settings.cors_origins.split(",") if item.strip()],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "migrateflow"}

    @application.get("/api/health", tags=["system"])
    def api_health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(batches_router)
    application.include_router(mappings_router)
    application.include_router(workflow_router)
    application.include_router(records_router)

    return application


app = create_app()
