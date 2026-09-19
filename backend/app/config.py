from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./migrateflow.db"
    upload_root: str = "./uploads"
    max_upload_files: int = 10
    max_upload_bytes: int = 10 * 1024 * 1024
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    model_mode: str = "ollama"
    demo_failures: bool = False
    cors_origins: str = "http://localhost:5173"
    max_model_prompt_chars: int = 12000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
