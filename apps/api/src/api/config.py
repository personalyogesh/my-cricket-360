from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Existing Supabase project — never create a replacement project for this app.
SUPABASE_PROJECT_NAME_EXPECTED = "mycricket360"
SUPABASE_ORG_EXPECTED = "personalyogesh"

# apps/api/src/api/config.py → repo root is parents[4]
REPO_ROOT = Path(__file__).resolve().parents[4]
API_ROOT = Path(__file__).resolve().parents[2]


def _env_files() -> tuple[str, ...]:
    """Environment-specific dotenv search paths (first existing wins per key via later override)."""
    env_name = os.getenv("MC360_ENV", "local")
    candidates = [
        REPO_ROOT / ".env",
        REPO_ROOT / f".env.{env_name}",
        API_ROOT / ".env",
        API_ROOT / f".env.{env_name}",
        REPO_ROOT / "config" / "environments" / f"{env_name}.env",
    ]
    return tuple(str(path) for path in candidates if path.is_file())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files() or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="local", alias="MC360_ENV")
    database_url: str = Field(
        default="sqlite+pysqlite:///./mc360-local.db",
        alias="MC360_DATABASE_URL",
    )
    cors_origins: str = Field(
        default=(
            "http://localhost:43123,http://127.0.0.1:43123,"
            "http://starks.localhost:43123,http://steelers.localhost:43123"
        ),
        alias="MC360_CORS_ORIGINS",
    )

    # Supabase Auth / JWT / Storage (server)
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_audience: str = Field(default="authenticated", alias="SUPABASE_JWT_AUDIENCE")
    supabase_jwt_issuer: str = Field(default="", alias="SUPABASE_JWT_ISSUER")
    supabase_jwks_url: str = Field(default="", alias="SUPABASE_JWKS_URL")
    supabase_project_name: str = Field(
        default=SUPABASE_PROJECT_NAME_EXPECTED,
        alias="SUPABASE_PROJECT_NAME",
    )
    supabase_org_slug: str = Field(default=SUPABASE_ORG_EXPECTED, alias="SUPABASE_ORG_SLUG")

    auth_mode: str = Field(default="auto", alias="MC360_AUTH_MODE")  # auto|supabase|dev
    dev_jwt_secret: str = Field(
        default="mc360-local-dev-only-not-for-production",
        alias="MC360_DEV_JWT_SECRET",
    )

    storage_backend: str = Field(default="auto", alias="MC360_STORAGE_BACKEND")
    local_storage_dir: str = Field(default=".local-storage", alias="MC360_LOCAL_STORAGE_DIR")
    supabase_storage_bucket: str = Field(default="sponsor-assets", alias="SUPABASE_STORAGE_BUCKET")
    max_upload_bytes: int = Field(default=2_000_000, alias="MC360_MAX_UPLOAD_BYTES")

    @field_validator("supabase_service_role_key")
    @classmethod
    def _service_role_not_anon_labelled(cls, value: str) -> str:
        # Soft check: service role keys are JWT-like; we mainly guard misuse via docs + client code.
        return value.strip()

    @model_validator(mode="after")
    def _reject_service_role_in_anon_slot(self) -> Settings:
        # If someone pasted service_role into ANON by mistake, fail fast in non-dev.
        anon = self.supabase_anon_key
        service = self.supabase_service_role_key
        if anon and service and anon == service:
            raise ValueError(
                "SUPABASE_ANON_KEY must not equal SUPABASE_SERVICE_ROLE_KEY "
                "(publishable vs server secret)."
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def jwt_issuer(self) -> str:
        if self.supabase_jwt_issuer:
            return self.supabase_jwt_issuer.rstrip("/")
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1"
        return "http://local.supabase.auth/auth/v1"

    @property
    def jwks_url(self) -> str:
        if self.supabase_jwks_url:
            return self.supabase_jwks_url
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return ""

    @property
    def supabase_host(self) -> str | None:
        if not self.supabase_url:
            return None
        return urlparse(self.supabase_url).hostname

    @property
    def database_name_hint(self) -> str | None:
        """Best-effort DB name from MC360_DATABASE_URL path (verify in Supabase UI)."""
        if not self.database_url or self.database_url.startswith("sqlite"):
            return None
        path = urlparse(self.database_url).path.lstrip("/")
        return path.split("?")[0] or None

    @property
    def effective_auth_mode(self) -> str:
        if self.auth_mode != "auto":
            return self.auth_mode
        if self.supabase_url and self.jwks_url:
            return "supabase"
        return "dev"

    @property
    def effective_storage_backend(self) -> str:
        if self.storage_backend != "auto":
            return self.storage_backend
        if self.supabase_url and self.supabase_service_role_key:
            return "supabase"
        return "local"

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
