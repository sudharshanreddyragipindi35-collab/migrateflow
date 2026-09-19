from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_args(url: str) -> dict[str, object]:
    return {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}


settings = get_settings()
engine = create_engine(settings.database_url, **_engine_args(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app.db import tables  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if str(engine.url).startswith("sqlite"):
        with engine.begin() as connection:
            connection.execute(text("CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_events BEGIN SELECT RAISE(FAIL, 'audit events are append only'); END"))
            connection.execute(text("CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_events BEGIN SELECT RAISE(FAIL, 'audit events are append only'); END"))


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
