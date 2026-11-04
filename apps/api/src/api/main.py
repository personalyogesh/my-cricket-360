from __future__ import annotations

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api import __version__
from api.clubs import (
    CLUBS_BY_SLUG,
    PLATFORM_HOSTS,
    get_club,
    normalize_host,
    resolve_club_slug_from_host,
)
from api.schemas import (
    HealthResponse,
    HostResolveResponse,
    OrganizationPublic,
    SponsorPublic,
)

app = FastAPI(
    title="My Cricket 360 API",
    version=__version__,
    description="Organization-scoped cricket management API for founding clubs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:43123",
        "http://127.0.0.1:43123",
        "http://starks.localhost:43123",
        "http://steelers.localhost:43123",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _org_public(slug: str) -> OrganizationPublic:
    club = get_club(slug)
    if club is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationPublic(
        id=club.organization_id,
        slug=club.slug,
        name=club.name,
        short_name=club.short_name,
        primary_domain=club.primary_domain,
        initial_sponsor=SponsorPublic(
            slug=club.initial_sponsor.slug,
            name=club.initial_sponsor.name,
            tagline=club.initial_sponsor.tagline,
            website_url=club.initial_sponsor.website_url,
        ),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="my-cricket-360-api", version=__version__)


@app.get("/v1/orgs", response_model=list[OrganizationPublic])
def list_organizations() -> list[OrganizationPublic]:
    return [_org_public(slug) for slug in CLUBS_BY_SLUG]


@app.get("/v1/orgs/{slug}", response_model=OrganizationPublic)
def get_organization(slug: str) -> OrganizationPublic:
    return _org_public(slug)


@app.get("/v1/resolve-host", response_model=HostResolveResponse)
def resolve_host(
    host: str = Query(..., description="Hostname to resolve (allowlisted only)"),
) -> HostResolveResponse:
    """Resolve a hostname using the server allowlist. Unknown → kind=unknown."""
    hostname = normalize_host(host)
    if not hostname:
        return HostResolveResponse(hostname="", kind="unknown", organization=None)

    if hostname in PLATFORM_HOSTS:
        return HostResolveResponse(hostname=hostname, kind="platform", organization=None)

    slug = resolve_club_slug_from_host(hostname)
    if slug is None:
        return HostResolveResponse(hostname=hostname, kind="unknown", organization=None)

    return HostResolveResponse(
        hostname=hostname,
        kind="club",
        organization=_org_public(slug),
    )


def run() -> None:
    uvicorn.run("api.main:app", host="0.0.0.0", port=8400, reload=True)


if __name__ == "__main__":
    run()
