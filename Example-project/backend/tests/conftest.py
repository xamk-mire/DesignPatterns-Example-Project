"""Point pytest at greenhouse_test before application settings are imported."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy.engine.url import make_url

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _BACKEND_DIR.parent
_TEST_DATABASE = "greenhouse_test"


def _read_database_url() -> str:
    configured = os.environ.get("DATABASE_URL")
    if configured:
        return configured
    env_path = _PROJECT_ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DATABASE_URL is not set")


os.environ["DATABASE_URL"] = make_url(_read_database_url()).set(database=_TEST_DATABASE).render_as_string(
    hide_password=False
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from infrastructure.db import SessionLocal  # noqa: E402
from infrastructure.dev_seed import SeedData, seed_database, truncate_business_tables  # noqa: E402


def _ensure_test_database() -> None:
    admin_url = make_url(os.environ["DATABASE_URL"]).set(database="postgres")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": _TEST_DATABASE},
        ).scalar()
        if exists is None:
            connection.execute(text(f"CREATE DATABASE {_TEST_DATABASE}"))
    engine.dispose()


def _upgrade_head() -> None:
    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> None:
    _ensure_test_database()
    _upgrade_head()


@pytest.fixture(autouse=True)
def seed(prepare_test_database: None) -> Generator[SeedData, None, None]:
    session = SessionLocal()
    try:
        truncate_business_tables(session)
        data = seed_database(session)
    finally:
        session.close()
    yield data
    session = SessionLocal()
    try:
        truncate_business_tables(session)
    finally:
        session.close()
