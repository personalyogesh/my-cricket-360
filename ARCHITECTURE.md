# My Cricket 360 — Architecture

## 1. System Overview

```
                    ┌─────────────────────────────────────┐
                    │     Clients                         │
                    │  Next.js (multi-host) │ SwiftUI iOS │
                    └───────────┬─────────────┬───────────┘
                                │             │
                         HTTPS  │             │ HTTPS + JWT
                                ▼             ▼
                    ┌─────────────────────────────────────┐
                    │  apps/api  (FastAPI + OpenAPI)      │
                    │  Org context · RBAC · Business logic│
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │  Supabase                           │
                    │  PostgreSQL · Auth · Storage        │
                    └─────────────────────────────────────┘
```

**One monorepo, one web app, one API, one iOS app, one database.** Club identity is an organization row; web branding is hostname → organization.

---

## 2. Repository Layout

```
my-cricket-360/
├── apps/
│   ├── web/                 # Next.js App Router (TypeScript, Tailwind)
│   ├── api/                 # FastAPI + SQLAlchemy 2 + Alembic
│   └── ios/                 # SwiftUI (Xcode project / SPM)
├── packages/
│   └── openapi/             # Published OpenAPI spec + generated clients (later)
├── docs/                    # Supplementary design notes
├── .github/workflows/       # CI/CD
├── .cursor/rules/           # Project Cursor rules
├── docker-compose.yml       # Local Postgres (optional when not using remote Supabase)
├── PRODUCT_REQUIREMENTS.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── IMPLEMENTATION_PLAN.md
└── README.md
```

---

## 3. Web: Hostname → Club Resolution

### 3.1 Allowlist (server-side)

Club resolution uses a **compile-time / env-loaded allowlist**, not free-form Host parsing for security decisions.

| Hostname | Organization slug | Primary canonical host |
|----------|-------------------|------------------------|
| `starksgroup.org` | `starks` | `starksgroup.org` |
| `www.starksgroup.org` | `starks` | `starksgroup.org` |
| `starks.localhost` | `starks` | (local) |
| `cgisteelerscricket.org` | `steelers` | `cgisteelerscricket.org` |
| `www.cgisteelerscricket.org` | `steelers` | `cgisteelerscricket.org` |
| `steelers.localhost` | `steelers` | (local) |
| `localhost` / `127.0.0.1` | platform / chooser | — |

Implementation sketch:

1. Normalize host (lowercase, strip port).
2. Lookup in `CLUB_HOST_ALLOWLIST`.
3. Miss → platform landing or HTTP 404; **never** default to another club’s org id.
4. Attach `ClubConfig` (slug, theme, logos, feature flags) to the request via Next.js `proxy.ts` request headers and `headers()` in RSC.

Security rules:

- Do **not** trust client-provided `?club=` for authorization or private data.
- Public pages may only load data for the allowlisted org.
- Admin APIs require JWT + membership role for that org, independent of hostname (hostname still scopes UX).

### 3.2 Branding & SEO

- Theme tokens (CSS variables), logo URLs, sponsor strip from `ClubConfig` + DB content.
- `generateMetadata` / canonical / OG tags use the club’s **primary domain**.
- Sitemaps generated per host.

### 3.3 Deployment model

- **One** Next.js deployment (Vercel or equivalent) with multiple domains attached in staging/production **after approval**.
- Until cutover: local + staging only; production DNS unchanged.

---

## 4. API: FastAPI Backend

### Responsibilities

- OpenAPI-first routes under `/v1`.
- Validate Supabase JWT (or service role for internal jobs).
- Resolve organization context from path/header **after** authz checks against membership tables.
- Enforce RBAC: `platform_admin`, `org_admin`, `org_member`, `public`.
- Sponsor CRUD, approval, analytics event ingest.
- Storage signed URLs via Supabase Storage (admin uploads).

### Stack

- Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2.
- Pytest for unit/integration tests.
- Uvicorn locally; containerizable for staging/prod.

### AuthZ pattern

```
Request → JWT verify (Supabase JWKS or local HS256) →
  ensure profile → load memberships →
  require org_id in memberships with required role →
  query always filtered by org_id
```

Self-approval of memberships is rejected. Sponsor mutations require **approved org admin** for that organization only.

Hostname is a **web concern**. Clients call `/v1/orgs/{slug}/...`; the API verifies membership independently of Host headers.

### Storage

- Supabase Storage bucket `sponsor-assets` when credentials exist.
- Local disk fallback under `MC360_LOCAL_STORAGE_DIR` served at `/v1/media/...`.
- Paths: `{organization_id}/{sponsor_id}/{asset_id}.ext` — never cross-org.

---

## 5. Data & Supabase

- Single existing Supabase project: **`mycricket360`** (org **`personalyogesh`**). Do not create another; do not touch Firebase.
- Project name ≠ Postgres database name — verify DB name under Settings → Database (often `postgres`).
- Publishable anon key only in Next.js (`NEXT_PUBLIC_*`) and iOS Info.plist/xcconfig.
- `service_role` and `MC360_DATABASE_URL` stay on the FastAPI server.
- Storage bucket: `sponsor-assets` — paths prefixed by `organization_id`.
- Auth: Supabase JWT via JWKS; local HS256 only when Supabase is not configured.
- See [config/SUPABASE.md](./config/SUPABASE.md).

See [DATA_MODEL.md](./DATA_MODEL.md).

---

## 6. iOS Architecture

- SwiftUI app target **My Cricket 360**.
- Modules (folders initially): `App`, `Auth`, `Clubs`, `Home`, `Sponsors`, `Matches`, `Networking`.
- Networking: URLSession + generated OpenAPI client (phase 2); hand-written DTOs in shell.
- Club switcher: `@AppStorage` / Keychain for last `organizationId`; refresh memberships on launch.
- No client-only authz for finances or admin actions.

---

## 7. Environments

| Env | Web | API | DB/Auth |
|-----|-----|-----|---------|
| local | `*.localhost` + port | `localhost:8400` | Docker Postgres or local Supabase |
| staging | staging hostnames | staging API URL | Staging Supabase |
| production | founding domains (post-approval) | prod API | Prod Supabase |

Config via `.env.local`, `.env.staging`, `.env.production` examples (secrets not committed).

---

## 8. CI/CD (GitHub Actions)

- **PR / push:** web lint + typecheck + unit tests; API ruff/mypy + pytest; OpenAPI drift check (later).
- **Deploy:** manual/gated workflows for staging; production requires approval.
- iOS: build job optional on macOS runners later; local Xcode for now.

---

## 9. Extensibility (future clubs)

- `organizations` + `organization_domains` tables already multi-tenant.
- `entitlements` / `subscription_status` columns reserved; billing inactive.
- Adding a club = insert org + domain allowlist entry + theme assets — no new deploy of a separate app.

---

## 10. Cutover Principles

1. Build and verify on local/staging with founding club content mirrored.
2. Keep Firebase + current sites untouched until explicit go-live checklist.
3. Attach custom domains to the new web deployment only with approval.
4. Rollback = leave DNS on legacy sites.
