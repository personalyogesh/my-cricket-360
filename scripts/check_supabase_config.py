#!/usr/bin/env python3
"""Validate My Cricket 360 env wiring for Supabase project mycricket360.

Does not print secret values. Exits non-zero when required server keys are missing
for supabase auth mode.
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


def _mask(value: str) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-4:]} (len={len(value)})"


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    print("Supabase project binding")
    print(f"  expected project name: {SUPABASE_PROJECT_NAME_EXPECTED}")
    print(f"  expected org:          {SUPABASE_ORG_EXPECTED}")
    print(f"  configured name:       {settings.supabase_project_name}")
    print(f"  configured org:        {settings.supabase_org_slug}")
    print(f"  MC360_ENV:             {settings.env}")
    print(f"  auth_mode:             {settings.effective_auth_mode}")
    print(f"  storage_backend:       {settings.effective_storage_backend}")
    print(f"  supabase_host:         {settings.supabase_host or '(not set)'}")
    print(f"  anon key:              {_mask(settings.supabase_anon_key)}")
    print(f"  service_role key:      {_mask(settings.supabase_service_role_key)}")
    print(f"  database driver:       {'sqlite' if settings.database_url.startswith('sqlite') else 'postgres'}")
    print(f"  database_name_hint:    {settings.database_name_hint or '(sqlite/local or unset)'}")
    print()
    print("Reminders:")
    print("  - Project name mycricket360 is NOT necessarily the Postgres database name.")
    print("  - Verify DB name in Supabase → Settings → Database before migrating.")
    print("  - Do not run alembic against production without approval.")
    print("  - Public clients may only use URL + anon/publishable key.")

    errors: list[str] = []
    if settings.supabase_project_name != SUPABASE_PROJECT_NAME_EXPECTED:
        errors.append(
            f"SUPABASE_PROJECT_NAME={settings.supabase_project_name!r} "
            f"(expected {SUPABASE_PROJECT_NAME_EXPECTED!r})"
        )
    if settings.supabase_org_slug != SUPABASE_ORG_EXPECTED:
        errors.append(
            f"SUPABASE_ORG_SLUG={settings.supabase_org_slug!r} "
            f"(expected {SUPABASE_ORG_EXPECTED!r})"
        )
    if settings.effective_auth_mode == "supabase":
        if not settings.supabase_url:
            errors.append("SUPABASE_URL required for supabase auth mode")
        if not settings.supabase_anon_key:
            errors.append("SUPABASE_ANON_KEY required for supabase auth mode")
        if settings.env in {"staging", "production"} and not settings.supabase_service_role_key:
            errors.append("SUPABASE_SERVICE_ROLE_KEY required for staging/production storage/admin")
        if settings.database_name_hint == "mycricket360":
            errors.append(
                "MC360_DATABASE_URL database name looks like the project label "
                "'mycricket360' — verify the real Postgres DB name in Supabase settings "
                "(often 'postgres')."
            )

    # Public env sanity (if present in process env)
    public_anon = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    if public_anon and "service_role" in public_anon.lower():
        errors.append("NEXT_PUBLIC_SUPABASE_ANON_KEY must not contain a service_role key")
    if os.getenv("NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY"):
        errors.append("NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY must never be set")

    if settings.supabase_url:
        host = urlparse(settings.supabase_url).hostname or ""
        if host and not host.endswith(".supabase.co"):
            print(f"  note: host {host!r} is unusual for Supabase (expected *.supabase.co)")

    if errors:
        print("\nFAIL:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("\nOK (structure). Fill real secrets locally; none were printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
