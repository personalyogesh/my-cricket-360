# Supabase project binding — My Cricket 360

## Existing project (do not recreate)

| Field | Value |
|-------|--------|
| Organization | `personalyogesh` |
| **Project name** | `mycricket360` |
| Purpose | Auth, Postgres, Storage for My Cricket 360 |

Reuse this project for local (when pointed at it), staging, and production configurations. **Do not create another Supabase project** for this application.

## Project name ≠ PostgreSQL database name

Supabase **project name** (`mycricket360`) is a dashboard label.

The **Postgres database name** is shown under:

**Project Settings → Database → Connection string / Database settings**

On most Supabase projects the database name is `postgres`, but **verify it in the dashboard** before writing `MC360_DATABASE_URL`. Never assume the database name equals `mycricket360`.

Connection URL shape (password and host from Settings → Database):

```text
postgresql+psycopg://postgres.<PROJECT_REF>:<DB_PASSWORD>@aws-0-<REGION>.pooler.supabase.com:6543/<DB_NAME>
```

or the direct connection host also shown in the same settings page. Use the **pooler** URL for the API in most cases.

## Project URL / ref

**Project Settings → API**:

- Project URL → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL` / iOS `SUPABASE_URL`
- `anon` `public` key → publishable only (`SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, iOS `SUPABASE_ANON_KEY`)
- `service_role` `secret` → **API server only** (`SUPABASE_SERVICE_ROLE_KEY`) — never Next.js `NEXT_PUBLIC_*`, never iOS Info.plist

JWKS (no secret required to fetch public keys):

```text
{SUPABASE_URL}/auth/v1/.well-known/jwks.json
```

Issuer expected by the API:

```text
{SUPABASE_URL}/auth/v1
```

Audience: `authenticated`

## Storage

Create (or reuse) a private/public bucket named `sponsor-assets` (override with `SUPABASE_STORAGE_BUCKET`). Object paths must stay org-scoped: `{organization_id}/{sponsor_id}/...`.

## Migrations

Alembic lives in `apps/api/alembic`. Founding seeds are idempotent (`uv run python -m api.seed`).

**Do not run `alembic upgrade` against production without explicit approval.**

## Key placement

| Secret / value | API | Next.js | iOS |
|----------------|-----|---------|-----|
| Project URL | yes | `NEXT_PUBLIC_` only | Info.plist / xcconfig |
| anon / publishable key | yes | `NEXT_PUBLIC_` only | Info.plist / xcconfig |
| service_role | **yes only** | never | never |
| DB password / `MC360_DATABASE_URL` | **yes only** | never | never |
