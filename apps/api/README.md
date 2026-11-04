# My Cricket 360 API

FastAPI + SQLAlchemy 2 + Alembic backend with organization-scoped RBAC.

## Local run

```bash
cd apps/api
uv sync --all-extras
cp ../../.env.example ../../.env   # if needed
uv run uvicorn api.main:app --host 0.0.0.0 --port 8400 --reload
```

On local/test startup the API ensures schema + idempotent founding seeds (Starks, Steelers, draft sponsors).

Postgres:

```bash
uv run alembic upgrade head
uv run python -m api.seed
```

## Auth

- **Production/staging:** Supabase JWT via JWKS (`iss`, `aud`, signature).
- **Local without Supabase:** `MC360_AUTH_MODE=dev` HS256 tokens from `POST /v1/auth/dev-token`.

Promote an admin:

```bash
uv run python scripts/promote_admin.py --email admin@starks.local --org starks
```

## Tests

```bash
uv run pytest
uv run ruff check src tests
```

## OpenAPI

```bash
uv run python - <<'PY'
from pathlib import Path
import json
from api.main import app
Path("../../packages/openapi/openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n")
print("wrote packages/openapi/openapi.json")
PY
```
