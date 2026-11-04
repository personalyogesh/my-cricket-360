from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

# Force deterministic test settings before app import
os.environ["MC360_ENV"] = "test"
os.environ["MC360_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["MC360_AUTH_MODE"] = "dev"
os.environ["MC360_STORAGE_BACKEND"] = "local"
os.environ["MC360_LOCAL_STORAGE_DIR"] = "/tmp/mc360-test-storage"
os.environ["MC360_DEV_JWT_SECRET"] = "test-secret-not-for-prod-32chars!!"
os.environ["SUPABASE_JWT_AUDIENCE"] = "authenticated"
os.environ["SUPABASE_JWT_ISSUER"] = "http://local.supabase.auth/auth/v1"

from api.config import get_settings
from api.db import Base, get_db, reset_engine
from api.main import app
from api.models import Organization
from api.seed import seed_founding_data

get_settings.cache_clear()


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    reset_engine("sqlite+pysqlite:///:memory:")
    get_settings.cache_clear()
    from api import db as db_module

    Base.metadata.create_all(bind=db_module.engine)
    # Must use module attribute after reset_engine() replaces SessionLocal.
    session = db_module.SessionLocal()
    seed_founding_data(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=db_module.engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def starks(db: Session) -> Organization:
    return db.scalar(select(Organization).where(Organization.slug == "starks"))  # type: ignore[return-value]


@pytest.fixture()
def steelers(db: Session) -> Organization:
    return db.scalar(select(Organization).where(Organization.slug == "steelers"))  # type: ignore[return-value]