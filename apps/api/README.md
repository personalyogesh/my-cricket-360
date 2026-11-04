# My Cricket 360 API

FastAPI backend for organization-scoped cricket management.

## Local run

```bash
cd apps/api
uv sync --all-extras
uv run uvicorn api.main:app --host 0.0.0.0 --port 8400 --reload
```

Health: [http://127.0.0.1:8400/health](http://127.0.0.1:8400/health)  
OpenAPI: [http://127.0.0.1:8400/docs](http://127.0.0.1:8400/docs)

## Tests

```bash
uv run pytest
```
