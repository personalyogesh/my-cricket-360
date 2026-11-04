# My Cricket 360

Native iOS + web multi-club cricket management platform.

**Founding clubs:** Starks Cricket (`starksgroup.org`) · CGI Steelers Cricket (`cgisteelerscricket.org`)  
**Initial sponsors:** Hashtag India Cary · CGI

One monorepo · one Next.js app · one FastAPI API · one SwiftUI app · one PostgreSQL (Supabase).

> Existing production websites stay live. Do **not** change DNS or deploy to production without approval. Do **not** modify or delete existing Firebase projects.

## Docs

| Document | Purpose |
|----------|---------|
| [PRODUCT_REQUIREMENTS.md](./PRODUCT_REQUIREMENTS.md) | Product scope & MVP |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design |
| [DATA_MODEL.md](./DATA_MODEL.md) | PostgreSQL schema |
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | Phased delivery |

## Repository layout

```
apps/web     Next.js App Router (hostname → club branding)
apps/api     FastAPI + SQLAlchemy 2 + Alembic
apps/ios     SwiftUI My Cricket 360
packages/openapi
```

## Prerequisites

- Node.js 20+
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Docker (optional local Postgres on port **5433**)
- macOS + Xcode 15+ for iOS

## Local development

### 1. Install

```bash
cp .env.example .env
npm install
cd apps/api && uv sync --all-extras && cd ../..
```

### 2. Web (port 43123)

```bash
npm run dev:web
```

| URL | What you see |
|-----|----------------|
| [http://localhost:43123](http://localhost:43123) | Platform chooser |
| [http://starks.localhost:43123](http://starks.localhost:43123) | Starks Cricket + Hashtag India Cary |
| [http://steelers.localhost:43123](http://steelers.localhost:43123) | CGI Steelers + CGI |

Modern browsers resolve `*.localhost` to loopback. Club resolution uses a **server-side hostname allowlist** (apex + www + local). Unknown hosts never map to another club.

### 3. API (port 8400)

```bash
cd apps/api
uv run uvicorn api.main:app --host 0.0.0.0 --port 8400 --reload
```

- Health: http://127.0.0.1:8400/health  
- Swagger: http://127.0.0.1:8400/docs  

Optional DB:

```bash
docker compose up -d db
```

### 4. iOS

```bash
cd apps/ios
xcodegen generate   # brew install xcodegen
open MyCricket360.xcodeproj
```

See [apps/ios/README.md](./apps/ios/README.md).

## Tests

```bash
# Web — hostname allowlist / club resolution
npm run test:web

# API
cd apps/api && uv run pytest
```

## Environments

| Env | Config samples |
|-----|----------------|
| local | `.env.example` |
| staging | `.env.staging.example` |
| production | `.env.production.example` (gated) |

CI runs on GitHub Actions (`.github/workflows/ci.yml`). Production deploy and DNS cutover require explicit approval.

## Safety

- No unvalidated `Host` header for security decisions.
- Organization-scoped RBAC; no cross-club private data.
- Sponsor uploads/approval and analytics are first-class (seeded founding sponsors).
- Billing / third-party club onboarding designed but not activated.
