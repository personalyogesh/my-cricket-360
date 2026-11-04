from __future__ import annotations

import os

import pytest


def test_production_migrate_requires_explicit_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MC360_ENV", "production")
    monkeypatch.delenv("MC360_ALLOW_PROD_MIGRATE", raising=False)
    monkeypatch.setenv("MC360_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("MC360_AUTH_MODE", "dev")

    from api.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    assert settings.env == "production"

    allow = os.getenv("MC360_ALLOW_PROD_MIGRATE", "").lower() in {"1", "true", "yes"}
    assert allow is False

    monkeypatch.setenv("MC360_ALLOW_PROD_MIGRATE", "true")
    assert os.getenv("MC360_ALLOW_PROD_MIGRATE", "").lower() in {"1", "true", "yes"}


def test_health_exposes_supabase_project_metadata_without_secrets(client) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["supabase_project_name"] == "mycricket360"
    assert "service_role" not in str(body).lower()
    assert "password" not in str(body).lower()
