from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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

    # Supabase Auth / JWT
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_audience: str = Field(default="authenticated", alias="SUPABASE_JWT_AUDIENCE")
    # Optional override; defaults to {SUPABASE_URL}/auth/v1
    supabase_jwt_issuer: str = Field(default="", alias="SUPABASE_JWT_ISSUER")
    supabase_jwks_url: str = Field(default="", alias="SUPABASE_JWKS_URL")

    # Local/test HS256 fallback when Supabase JWKS is unavailable
    auth_mode: str = Field(default="auto", alias="MC360_AUTH_MODE")  # auto|supabase|dev
    dev_jwt_secret: str = Field(
        default="mc360-local-dev-only-not-for-production",
        alias="MC360_DEV_JWT_SECRET",
    )

    # Storage
    storage_backend: str = Field(default="auto", alias="MC360_STORAGE_BACKEND")  # auto|local|supabase
    local_storage_dir: str = Field(
        default=".local-storage",
        alias="MC360_LOCAL_STORAGE_DIR",
    )
    supabase_storage_bucket: str = Field(
        default="sponsor-assets",
        alias="SUPABASE_STORAGE_BUCKET",
    )
    max_upload_bytes: int = Field(default=2_000_000, alias="MC360_MAX_UPLOAD_BYTES")

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
    def effective_auth_mode(self) -> str:
        if self.auth_mode != "auto":
            return self.auth_mode
        if self.supabase_url and (self.jwks_url or self.supabase_jwt_issuer):
            return "supabase"
        return "dev"

    @property
    def effective_storage_backend(self) -> str:
        if self.storage_backend != "auto":
            return self.storage_backend
        if self.supabase_url and self.supabase_service_role_key:
            return "supabase"
        return "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
