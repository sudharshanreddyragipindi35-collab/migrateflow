import json
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(prefix="/api/system", tags=["system"])


class ModelRuntimeStatus(BaseModel):
    mode: str
    provider: str
    model: str | None
    status: str


def _ollama_status(base_url: str, model: str) -> str:
    try:
        with urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=2) as response:  # noqa: S310
            payload = json.load(response)
    except (OSError, URLError, ValueError):
        return "unavailable"
    installed = {item.get("name") for item in payload.get("models", [])}
    return "ready" if model in installed else "model_missing"


@router.get("/model", response_model=ModelRuntimeStatus)
def model_runtime() -> ModelRuntimeStatus:
    settings = get_settings()
    if settings.model_mode == "ollama":
        return ModelRuntimeStatus(
            mode="ollama",
            provider="Ollama",
            model=settings.ollama_model,
            status=_ollama_status(settings.ollama_base_url, settings.ollama_model),
        )
    if settings.model_mode == "anthropic":
        return ModelRuntimeStatus(
            mode="anthropic",
            provider="Anthropic",
            model=settings.anthropic_model,
            status="configured" if settings.anthropic_api_key.strip() else "misconfigured",
        )
    if settings.model_mode == "fallback":
        return ModelRuntimeStatus(
            mode="fallback",
            provider="Deterministic fallback",
            model=None,
            status="ready",
        )
    return ModelRuntimeStatus(
        mode=settings.model_mode,
        provider="Unknown",
        model=None,
        status="misconfigured",
    )
