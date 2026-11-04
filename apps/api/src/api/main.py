from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import __version__
from api.config import get_settings
from api.routers import auth_dev, me, media, orgs, sponsors
from api.schemas import HealthResponse
from api.seed import ensure_schema_and_seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    # Local/dev convenience: ensure schema + founding seeds exist.
    if settings.env in {"local", "test"} or settings.database_url.startswith("sqlite"):
        ensure_schema_and_seed()
    yield


app = FastAPI(
    title="My Cricket 360 API",
    version=__version__,
    description="Organization-scoped cricket management API for founding clubs.",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orgs.router)
app.include_router(me.router)
app.include_router(sponsors.router)
app.include_router(media.router)
app.include_router(auth_dev.router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    s = get_settings()
    driver = "sqlite" if s.database_url.startswith("sqlite") else "postgres"
    return HealthResponse(
        status="ok",
        service="my-cricket-360-api",
        version=__version__,
        auth_mode=s.effective_auth_mode,
        storage_backend=s.effective_storage_backend,
        supabase_configured=s.supabase_configured,
        supabase_host=s.supabase_host,
        supabase_project_name=s.supabase_project_name,
        database_driver=driver,
        database_name_hint=s.database_name_hint,
    )


def run() -> None:
    uvicorn.run("api.main:app", host="0.0.0.0", port=8400, reload=True)


if __name__ == "__main__":
    run()
