#!/usr/bin/env python3
"""Validate My Cricket 360 env wiring for Supabase project mycricket360.

Never prints secret values — only presence/absence and non-secret metadata.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

try:
    from api.config import (  # noqa: E402
        SUPABASE_ORG_EXPECTED,
        SUPABASE_PROJECT_NAME_EXPECTED,
        get_settings,
    )
except ModuleNotFoundError:
    print(
        "Missing API deps. Run:\n"
        "  cd apps/api && uv sync --all-extras\n"
        "  uv run python ../../scripts/check_supabase_config.py",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


def _present(value: str) -> str:
    return "set" if value.strip() else "MISSING"


def _key_kind(value: str) -> str:
    v = value.strip()
    if not v:
        return "n/a"
    if v.startswith("sb_publishable_"):
        return "new-publishable"
    if v.startswith("sb_secret_"):
        return "new-secret"
    if v.startswith("eyJ"):
        return "legacy-jwt"
    return "unknown-format"


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()

    print("=== Supabase binding ===")
    print(f"expected project: {SUPABASE_PROJECT_NAME_EXPECTED}")
    print(f"expected org:     {SUPABASE_ORG_EXPECTED}")
    print(f"configured name:  {settings.supabase_project_name}")
    print(f"configured org:   {settings.supabase_org_slug}")
    print(f"MC360_ENV:        {settings.env}")
    print(f"auth_mode:        {settings.effective_auth_mode}")
    print(f"storage_backend:  {settings.effective_storage_backend}")
    print(f"supabase_host:    {settings.supabase_host or '(not set)'}")
    print(f"database_driver:  {'sqlite' if settings.database_url.startswith('sqlite') else 'postgres'}")
    print(f"database_name_hint: {settings.database_name_hint or '(sqlite/local or unset)'}")

    print("\n=== Server variable presence (values hidden) ===")
    print(f"SUPABASE_URL:                 {_present(settings.supabase_url)}")
    print(f"SUPABASE_PUBLISHABLE_KEY:     {_present(settings.supabase_publishable_key)} [{_key_kind(settings.supabase_publishable_key)}]")
    print(f"SUPABASE_ANON_KEY:            {_present(settings.supabase_anon_key)} [{_key_kind(settings.supabase_anon_key)}]")
    print(f"effective publishable:        {_present(settings.publishable_key)} [{_key_kind(settings.publishable_key)}]")
    print(f"SUPABASE_SECRET_KEY:          {_present(settings.supabase_secret_key)} [{_key_kind(settings.supabase_secret_key)}]")
    print(f"SUPABASE_SERVICE_ROLE_KEY:    {_present(settings.supabase_service_role_key)} [{_key_kind(settings.supabase_service_role_key)}]")
    print(f"effective secret:             {_present(settings.secret_key)} [{_key_kind(settings.secret_key)}]")
    print(f"MC360_DATABASE_URL:           {_present(settings.database_url)}")

    print("\n=== Public client env presence (values hidden) ===")
    public_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    public_pub = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
    public_anon = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    print(f"NEXT_PUBLIC_SUPABASE_URL:              {_present(public_url)}")
    print(f"NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:  {_present(public_pub)} [{_key_kind(public_pub)}]")
    print(f"NEXT_PUBLIC_SUPABASE_ANON_KEY:         {_present(public_anon)} [{_key_kind(public_anon)}]")
    banned = os.getenv("NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
        "NEXT_PUBLIC_SUPABASE_SECRET_KEY", ""
    )
    print(f"NEXT_PUBLIC_* secret slots:            {'FORBIDDEN-IF-SET' if banned else 'absent (good)'}")

    print("\n=== Local credential files ===")
    for path in [
        ROOT / ".env",
        ROOT / "apps" / "web" / ".env.local",
        ROOT / "apps" / "api" / ".env",
        ROOT / "apps" / "ios" / "Config" / "Debug.xcconfig",
    ]:
        print(f"{path.relative_to(ROOT)}: {'exists' if path.exists() else 'missing'}")

    missing: list[str] = []
    errors: list[str] = []

    if settings.supabase_project_name != SUPABASE_PROJECT_NAME_EXPECTED:
        errors.append("SUPABASE_PROJECT_NAME mismatch")
    if settings.supabase_org_slug != SUPABASE_ORG_EXPECTED:
        errors.append("SUPABASE_ORG_SLUG mismatch")

    # Required to leave local/dev offline mode
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.publishable_key:
        missing.append("SUPABASE_PUBLISHABLE_KEY or SUPABASE_ANON_KEY")
    if not settings.secret_key:
        missing.append("SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY")
    if settings.database_url.startswith("sqlite"):
        missing.append("MC360_DATABASE_URL (Postgres from Supabase Settings → Database)")
    elif "REPLACE_WITH_DB_PASSWORD" in settings.database_url or "[YOUR-PASSWORD]" in settings.database_url:
        missing.append("MC360_DATABASE_URL password (replace placeholder from Settings → Database)")

    if settings.database_name_hint == "mycricket360":
        errors.append(
            "MC360_DATABASE_URL path uses 'mycricket360' — that is the project label, "
            "not necessarily the Postgres database name. Verify in Settings → Database."
        )

    if _key_kind(settings.publishable_key) == "new-secret":
        errors.append("effective publishable key looks like sb_secret_ (server-only)")
    if _key_kind(settings.secret_key) == "new-publishable":
        errors.append("effective secret key looks like sb_publishable_ (client key)")

    if banned:
        errors.append("NEXT_PUBLIC_ secret/service_role variable must never be set")

    effective_public = public_pub or public_anon
    if effective_public and _key_kind(effective_public) == "new-secret":
        errors.append("NEXT_PUBLIC publishable/anon slot contains sb_secret_")

    print("\n=== Result ===")
    if missing:
        print("MISSING (needed to use Supabase mycricket360 for real auth/DB/storage):")
        for item in missing:
            print(f"  - {item}")
    if errors:
        print("ERRORS:")
        for item in errors:
            print(f"  - {item}")
    if not missing and not errors:
        print("OK — required values appear present (contents not displayed).")
        print("Still verify Postgres database name in the Supabase dashboard before migrating.")
        return 0

    if missing and not errors:
        print(
            "Structure OK for offline/dev fallback, but Supabase is not fully configured yet."
        )
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
