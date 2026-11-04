from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure src/ is importable when running alembic from apps/api
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from api.config import get_settings  # noqa: E402
from api.db import Base  # noqa: E402
from api import models  # noqa: E402,F401 — register models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return get_settings().database_url


def _guard_production_migrate() -> None:
    """Refuse accidental production migrations unless explicitly allowed."""
    settings = get_settings()
    allow = os.getenv("MC360_ALLOW_PROD_MIGRATE", "").lower() in {"1", "true", "yes"}
    if settings.env == "production" and not allow:
        raise RuntimeError(
            "Refusing Alembic against MC360_ENV=production without "
            "MC360_ALLOW_PROD_MIGRATE=true (explicit approval required)."
        )


def run_migrations_offline() -> None:
    _guard_production_migrate()
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _guard_production_migrate()
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
