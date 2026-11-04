from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.clubs import PLATFORM_HOSTS, normalize_host, resolve_club_slug_from_host
from api.db import get_db
from api.models import Organization, Sponsor
from api.schemas import HostResolveResponse, OrganizationPublic
from api.services import org_to_public
from api.storage import StorageService

router = APIRouter(tags=["organizations"])


def _founding_sponsor(db: Session, org_id) -> Sponsor | None:
    return db.scalar(
        select(Sponsor)
        .where(Sponsor.organization_id == org_id)
        .order_by(Sponsor.sort_order.asc(), Sponsor.created_at.asc())
        .limit(1)
    )


@router.get("/v1/orgs", response_model=list[OrganizationPublic])
def list_organizations(db: Session = Depends(get_db)) -> list[OrganizationPublic]:
    orgs = db.scalars(select(Organization).order_by(Organization.slug.asc())).all()
    storage = StorageService()
    return [
        org_to_public(org, founding_sponsor=_founding_sponsor(db, org.id), storage=storage)
        for org in orgs
    ]


@router.get("/v1/orgs/{slug}", response_model=OrganizationPublic)
def get_organization(slug: str, db: Session = Depends(get_db)) -> OrganizationPublic:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org_to_public(
        org,
        founding_sponsor=_founding_sponsor(db, org.id),
        storage=StorageService(),
    )


@router.get("/v1/resolve-host", response_model=HostResolveResponse)
def resolve_host(
    host: str = Query(..., description="Hostname to resolve (allowlisted only)"),
    db: Session = Depends(get_db),
) -> HostResolveResponse:
    hostname = normalize_host(host)
    if not hostname:
        return HostResolveResponse(hostname="", kind="unknown", organization=None)
    if hostname in PLATFORM_HOSTS:
        return HostResolveResponse(hostname=hostname, kind="platform", organization=None)

    slug = resolve_club_slug_from_host(hostname)
    if slug is None:
        return HostResolveResponse(hostname=hostname, kind="unknown", organization=None)

    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        return HostResolveResponse(hostname=hostname, kind="unknown", organization=None)

    return HostResolveResponse(
        hostname=hostname,
        kind="club",
        organization=org_to_public(
            org,
            founding_sponsor=_founding_sponsor(db, org.id),
            storage=StorageService(),
        ),
    )
