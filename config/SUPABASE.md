# Supabase project binding — My Cricket 360

## Existing project (do not recreate)

| Field | Value |
|-------|--------|
| Organization | `personalyogesh` |
| **Project name** | `mycricket360` |
| Purpose | Auth, Postgres, Storage for My Cricket 360 |

Reuse this project. **Do not create another Supabase project.** Do not modify Firebase.

## Project name ≠ PostgreSQL database name

`mycricket360` is a **dashboard project label**.

The **Postgres database name** is under:

**Project Settings → Database** (connection string / database name)

Often it is `postgres`. **Always verify** before setting `MC360_DATABASE_URL`. Never assume the DB name equals `mycricket360`.

### Recommended API connection

Prefer the **connection pooler** URI from Settings → Database (Transaction mode for serverless/API). Rewrite the scheme for SQLAlchemy/psycopg:

```text
postgresql+psycopg://…@…pooler.supabase.com:6543/<VERIFIED_DB_NAME>
```

Direct `db.<ref>.supabase.co:5432` also works for long-lived local processes.

## API keys: new vs legacy

Supabase now ships **publishable** / **secret** keys and still supports legacy **anon** / **service_role** JWTs (deprecated by end of 2026). Both work with `@supabase/supabase-js` **v2.118.x** installed in `apps/web`.

| Privilege | New (preferred) | Legacy | Where it goes |
|-----------|-----------------|--------|----------------|
| Low (public) | `sb_publishable_…` | `anon` JWT (`eyJ…`) | Web `NEXT_PUBLIC_*`, iOS xcconfig, API publishable slot |
| Elevated (server) | `sb_secret_…` | `service_role` JWT | **API only** |

Dashboard: **Project Settings → API Keys** (Publishable and secret tab; legacy keys may appear under a Legacy tab).

This repo accepts either naming in env:

| Role | Preferred env | Legacy env alias |
|------|---------------|------------------|
| Public | `SUPABASE_PUBLISHABLE_KEY` / `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | `SUPABASE_ANON_KEY` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
| Server | `SUPABASE_SECRET_KEY` | `SUPABASE_SERVICE_ROLE_KEY` |

## Per-app environment variables

### FastAPI (`apps/api`) — server only

| Variable | Required for Supabase mode | Notes |
|----------|----------------------------|-------|
| `SUPABASE_URL` | yes | Project URL |
| `SUPABASE_PUBLISHABLE_KEY` or `SUPABASE_ANON_KEY` | yes | For config completeness / future client-style calls |
| `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY` | yes (storage) | Storage uploads; never expose |
| `MC360_DATABASE_URL` | yes (real DB) | Postgres URL with **verified** DB name |
| `SUPABASE_JWT_AUDIENCE` | default `authenticated` | User JWT `aud` |
| `SUPABASE_JWT_ISSUER` | optional | Defaults to `{URL}/auth/v1` |
| `SUPABASE_JWKS_URL` | optional | Defaults to `{URL}/auth/v1/.well-known/jwks.json` |
| `SUPABASE_STORAGE_BUCKET` | default `sponsor-assets` | |
| `MC360_AUTH_MODE` | `auto` or `supabase` | |
| `MC360_ENV` | `local` / `staging` / `production` | Production migrations gated |

User access tokens are validated via **JWKS** (not by embedding the secret key in JWT checks).

### Next.js (`apps/web`) — publishable only

| Variable | Required | Notes |
|----------|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | yes | |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` or `NEXT_PUBLIC_SUPABASE_ANON_KEY` | yes | |
| `NEXT_PUBLIC_API_BASE_URL` | yes | FastAPI base |

**Forbidden in web:** any `NEXT_PUBLIC_*` secret/service_role, `MC360_DATABASE_URL`, DB passwords.

### SwiftUI (`apps/ios`) — publishable only via gitignored xcconfig

| Info.plist / xcconfig key | Required | Notes |
|---------------------------|----------|-------|
| `SUPABASE_URL` | yes | |
| `SUPABASE_PUBLISHABLE_KEY` or `SUPABASE_ANON_KEY` | yes | |
| `MC360APIBaseURL` | yes | API base |

**Forbidden on device:** secret/service_role, database URL/password.

Tracked `Info.plist` only contains `$(VAR)` placeholders. Real values live in `apps/ios/Config/*.xcconfig` (**gitignored**).

## JWT / Auth wiring

1. Web/iOS sign in with Supabase Auth using the **publishable** key.
2. Clients send `Authorization: Bearer <user access_token>` to FastAPI.
3. FastAPI verifies the user JWT with JWKS (`iss` + `aud=authenticated`).

## Storage

Create bucket `sponsor-assets` (or set `SUPABASE_STORAGE_BUCKET`). Paths: `{organization_id}/{sponsor_id}/...`. Uploads use the **server secret** key from FastAPI only.

## Migrations

Alembic: `apps/api/alembic`. Seeds: `uv run python -m api.seed` (idempotent Starks/Steelers).

**Do not run against production without approval.** `MC360_ENV=production` requires `MC360_ALLOW_PROD_MIGRATE=true`.

## Validate (no secret printing)

```bash
cd apps/api && uv run python ../../scripts/check_supabase_config.py
```
