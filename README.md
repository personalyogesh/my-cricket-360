# My Cricket 360

Native iOS + web multi-club cricket management platform.

**Founding clubs:** Starks Cricket (`starksgroup.org`) · CGI Steelers Cricket (`cgisteelerscricket.org`)  
**Initial sponsors (seeded as draft):** Hashtag India Cary · CGI

One monorepo · one Next.js app · one FastAPI API · one SwiftUI app · one PostgreSQL (Supabase).

> Existing production websites stay live. Do **not** change DNS or deploy to production without approval. Do **not** modify or delete existing Firebase projects.

## Docs

| Document | Purpose |
|----------|---------|
| [PRODUCT_REQUIREMENTS.md](./PRODUCT_REQUIREMENTS.md) | Product scope & MVP |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design |
| [DATA_MODEL.md](./DATA_MODEL.md) | PostgreSQL schema |
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | Phased delivery |
| [packages/openapi/openapi.json](./packages/openapi/openapi.json) | Generated OpenAPI |

## Repository layout

```
apps/web     Next.js App Router (hostname → club branding + admin)
apps/api     FastAPI + SQLAlchemy 2 + Alembic
apps/ios     SwiftUI My Cricket 360
packages/openapi
```

## Prerequisites

- Node.js 20+
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Docker (optional Postgres on port **5433**)
- macOS + Xcode 15+ for iOS (`xcodegen`)

## Local development

### 1. Install

```bash
cp .env.example .env
npm install
cd apps/api && uv sync --all-extras && cd ../..
```

### 2. Database

**SQLite (default local):** created automatically on API startup (`mc360-local.db`) with idempotent founding seeds.

**Postgres (recommended when Docker works):**

```bash
docker compose up -d db
# set MC360_DATABASE_URL=postgresql+psycopg://mc360:mc360@127.0.0.1:5433/mc360
cd apps/api
uv run alembic upgrade head
uv run python -m api.seed
```

### 3. API (port 8400)

```bash
cd apps/api
uv run uvicorn api.main:app --host 0.0.0.0 --port 8400 --reload
```

- Health: http://127.0.0.1:8400/health  
- Swagger: http://127.0.0.1:8400/docs  

Promote a local admin (after first login/dev-token creates the profile, or with a fresh email):

```bash
cd apps/api
uv run python scripts/promote_admin.py --email admin@starks.local --org starks
```

### 4. Web (port 43123)

```bash
npm run dev:web
```

| URL | What you see |
|-----|----------------|
| [http://localhost:43123](http://localhost:43123) | Platform chooser |
| [http://starks.localhost:43123](http://starks.localhost:43123) | Starks Cricket |
| [http://steelers.localhost:43123](http://steelers.localhost:43123) | CGI Steelers |
| `/admin/login` on a club host | Admin login (Supabase or local dev token) |
| `/admin/sponsors` | Club-scoped sponsor management |

Public sponsor pages only show **published** sponsors. Founding seeds remain **draft** until an admin verifies and publishes them (no fabricated logos).

### 5. iOS

```bash
cd apps/ios
xcodegen generate
open MyCricket360.xcodeproj
```

The shell talks to `http://127.0.0.1:8400` (Keychain token + membership requests + published sponsors). **No iOS compile was run in Linux CI** — verify on macOS/Xcode.

## Tests

```bash
# Web — hostname allowlist
npm run test:web
npm run lint -w @my-cricket-360/web

# API — seeds, authz, sponsors
cd apps/api && uv run pytest && uv run ruff check src tests
```

## Supabase configuration (existing project)

**Reuse** Supabase project **`mycricket360`** in organization **`personalyogesh`**. Do not create another project. Do not touch Firebase.

Full notes: [config/SUPABASE.md](./config/SUPABASE.md) · env templates: [config/environments/](./config/environments/)

| Setting | Where |
|---------|--------|
| Project URL | Settings → API → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL` / iOS `SUPABASE_URL` |
| anon **publishable** key | Settings → API → public clients + API anon |
| service_role **secret** | API only (`SUPABASE_SERVICE_ROLE_KEY`) — never `NEXT_PUBLIC_*`, never iOS |
| Postgres DB name | Settings → Database (**not** the project label `mycricket360`; often `postgres`) |
| `MC360_DATABASE_URL` | API server only |
| JWKS | `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` |
| Storage bucket | `sponsor-assets` |

```bash
# After filling .env from the dashboard (never commit it):
python scripts/check_supabase_config.py
# Migrate non-production only, then seed:
cd apps/api && uv run alembic upgrade head && uv run python -m api.seed
# Production migrations require explicit approval + MC360_ALLOW_PROD_MIGRATE=true
```

Without credentials, the API runs **dev auth** (HS256) + **local disk storage**.

## GitHub and Vercel

Source of truth: [github.com/personalyogesh/my-cricket-360](https://github.com/personalyogesh/my-cricket-360).

- Land work on a branch and open a pull request into `main`. GitHub Actions (web lint, test, build, and API tests) must pass. `main` does not take direct feature pushes.
- Vercel builds **only** the Next.js app. Import this repository and set **Root Directory** to `apps/web` (`apps/web/vercel.json`). Pull requests get preview deployments. A production deployment runs only after the pull request is merged to `main`.
- Do not attach `starksgroup.org` or `cgisteelerscricket.org` until a DNS cutover is explicitly approved. Set `NEXT_PUBLIC_*` values from `apps/web/.env.local.example` in the Vercel project. Never put the Supabase secret key or database URL on the web project.
- The SwiftUI app in `apps/ios` is built with Xcode on macOS from this same repository. Vercel does not compile it.

## Safety

- Hostname allowlist only for web club resolution.
- Organization-scoped RBAC; Steelers admins cannot mutate Starks sponsors (and vice versa).
- No secrets in git; no DNS/production deploy without approval.
