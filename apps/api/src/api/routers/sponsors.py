from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthUser, get_current_user, require_org_admin
from api.db import get_db
from api.models import Organization, Sponsor, SponsorAsset, utcnow
from api.schemas import (
    SponsorAdminOut,
    SponsorAssetOut,
    SponsorCreateIn,
    SponsorPublic,
    SponsorUpdateIn,
)
from api.services import sponsor_to_admin, sponsor_to_public, touch, write_audit
from api.storage import StorageService, build_storage_path, read_validated_image

router = APIRouter(tags=["sponsors"])

PUBLIC_STATUSES = {"published"}


def _get_org(db: Session, slug: str) -> Organization:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def _get_sponsor_for_org(db: Session, org: Organization, sponsor_slug: str) -> Sponsor:
    sponsor = db.scalar(
        select(Sponsor).where(
            Sponsor.organization_id == org.id,
            Sponsor.slug == sponsor_slug,
        )
    )
    if sponsor is None:
        raise HTTPException(status_code=404, detail="Sponsor not found")
    return sponsor


@router.get("/v1/orgs/{slug}/sponsors", response_model=list[SponsorPublic])
def list_public_sponsors(slug: str, db: Session = Depends(get_db)) -> list[SponsorPublic]:
    org = _get_org(db, slug)
    sponsors = db.scalars(
        select(Sponsor)
        .where(Sponsor.organization_id == org.id, Sponsor.status.in_(tuple(PUBLIC_STATUSES)))
        .order_by(Sponsor.sort_order.asc(), Sponsor.name.asc())
    ).all()
    storage = StorageService()
    return [sponsor_to_public(s, storage) for s in sponsors]


@router.get("/v1/orgs/{slug}/sponsors/{sponsor_slug}", response_model=SponsorPublic)
def get_public_sponsor(
    slug: str, sponsor_slug: str, db: Session = Depends(get_db)
) -> SponsorPublic:
    org = _get_org(db, slug)
    sponsor = _get_sponsor_for_org(db, org, sponsor_slug)
    if sponsor.status not in PUBLIC_STATUSES:
        raise HTTPException(status_code=404, detail="Sponsor not found")
    return sponsor_to_public(sponsor)


@router.get("/v1/orgs/{slug}/admin/sponsors", response_model=list[SponsorAdminOut])
def list_admin_sponsors(
    slug: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SponsorAdminOut]:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    sponsors = db.scalars(
        select(Sponsor)
        .where(Sponsor.organization_id == org.id)
        .order_by(Sponsor.sort_order.asc(), Sponsor.name.asc())
    ).all()
    storage = StorageService()
    return [sponsor_to_admin(s, storage) for s in sponsors]


@router.post(
    "/v1/orgs/{slug}/admin/sponsors",
    response_model=SponsorAdminOut,
    status_code=201,
)
def create_sponsor(
    slug: str,
    body: SponsorCreateIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SponsorAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    exists = db.scalar(
        select(Sponsor).where(Sponsor.organization_id == org.id, Sponsor.slug == body.slug)
    )
    if exists is not None:
        raise HTTPException(status_code=409, detail="Sponsor slug already exists for this club")

    sponsor = Sponsor(
        organization_id=org.id,
        slug=body.slug,
        name=body.name,
        tagline=body.tagline,
        description=body.description,
        website_url=body.website_url,
        sort_order=body.sort_order,
        status="draft",
    )
    db.add(sponsor)
    db.flush()
    write_audit(
        db,
        action="sponsor.created",
        entity_type="sponsor",
        entity_id=str(sponsor.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"slug": sponsor.slug},
    )
    db.commit()
    db.refresh(sponsor)
    return sponsor_to_admin(sponsor)


@router.patch("/v1/orgs/{slug}/admin/sponsors/{sponsor_slug}", response_model=SponsorAdminOut)
def update_sponsor(
    slug: str,
    sponsor_slug: str,
    body: SponsorUpdateIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SponsorAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    sponsor = _get_sponsor_for_org(db, org, sponsor_slug)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(sponsor, key, value)
    touch(sponsor)
    write_audit(
        db,
        action="sponsor.updated",
        entity_type="sponsor",
        entity_id=str(sponsor.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta=data,
    )
    db.commit()
    db.refresh(sponsor)
    return sponsor_to_admin(sponsor)


@router.post(
    "/v1/orgs/{slug}/admin/sponsors/{sponsor_slug}/assets",
    response_model=SponsorAssetOut,
    status_code=201,
)
async def upload_sponsor_asset(
    slug: str,
    sponsor_slug: str,
    asset_type: str = Form(..., pattern="^(logo|banner)$"),
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SponsorAssetOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    sponsor = _get_sponsor_for_org(db, org, sponsor_slug)

    data, content_type, ext = await read_validated_image(file)
    asset_id = uuid.uuid4()
    storage_path = build_storage_path(
        organization_id=org.id,
        sponsor_id=sponsor.id,
        asset_id=asset_id,
        ext=ext,
    )
    storage = StorageService()
    await storage.put_bytes(storage_path, data, content_type)

    asset = SponsorAsset(
        id=asset_id,
        sponsor_id=sponsor.id,
        organization_id=org.id,
        asset_type=asset_type,
        storage_path=storage_path,
        content_type=content_type,
        byte_size=len(data),
        uploaded_by=user.id,
        status="approved",
    )
    db.add(asset)
    if asset_type == "logo":
        sponsor.logo_path = storage_path
    else:
        sponsor.banner_path = storage_path
    touch(sponsor)
    write_audit(
        db,
        action="sponsor.asset_uploaded",
        entity_type="sponsor_asset",
        entity_id=str(asset.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"asset_type": asset_type, "sponsor_id": str(sponsor.id)},
    )
    db.commit()
    db.refresh(asset)
    return SponsorAssetOut(
        id=asset.id,
        sponsor_id=asset.sponsor_id,
        organization_id=asset.organization_id,
        asset_type=asset.asset_type,
        storage_path=asset.storage_path,
        content_type=asset.content_type,
        byte_size=asset.byte_size,
        status=asset.status,
        url=storage.public_url(asset.storage_path),
    )


@router.post(
    "/v1/orgs/{slug}/admin/sponsors/{sponsor_slug}/approve",
    response_model=SponsorAdminOut,
)
def approve_sponsor(
    slug: str,
    sponsor_slug: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SponsorAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    sponsor = _get_sponsor_for_org(db, org, sponsor_slug)
    if sponsor.status in {"archived"}:
        raise HTTPException(status_code=400, detail="Archived sponsors cannot be approved")
    sponsor.status = "approved"
    sponsor.approved_at = utcnow()
    sponsor.approved_by = user.id
    touch(sponsor)
    write_audit(
        db,
        action="sponsor.approved",
        entity_type="sponsor",
        entity_id=str(sponsor.id),
        organization_id=org.id,
        actor_user_id=user.id,
    )
    db.commit()
    db.refresh(sponsor)
    return sponsor_to_admin(sponsor)


@router.post(
    "/v1/orgs/{slug}/admin/sponsors/{sponsor_slug}/publish",
    response_model=SponsorAdminOut,
)
def publish_sponsor(
    slug: str,
    sponsor_slug: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SponsorAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    sponsor = _get_sponsor_for_org(db, org, sponsor_slug)
    if sponsor.status not in {"approved", "published"}:
        raise HTTPException(
            status_code=400,
            detail="Sponsor must be approved before publishing",
        )
    sponsor.status = "published"
    sponsor.published_at = utcnow()
    sponsor.published_by = user.id
    touch(sponsor)
    write_audit(
        db,
        action="sponsor.published",
        entity_type="sponsor",
        entity_id=str(sponsor.id),
        organization_id=org.id,
        actor_user_id=user.id,
    )
    db.commit()
    db.refresh(sponsor)
    return sponsor_to_admin(sponsor)


@router.post(
    "/v1/orgs/{slug}/admin/sponsors/{sponsor_slug}/unpublish",
    response_model=SponsorAdminOut,
)
def unpublish_sponsor(
    slug: str,
    sponsor_slug: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SponsorAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    sponsor = _get_sponsor_for_org(db, org, sponsor_slug)
    if sponsor.status != "published":
        raise HTTPException(status_code=400, detail="Sponsor is not published")
    sponsor.status = "approved"
    touch(sponsor)
    write_audit(
        db,
        action="sponsor.unpublished",
        entity_type="sponsor",
        entity_id=str(sponsor.id),
        organization_id=org.id,
        actor_user_id=user.id,
    )
    db.commit()
    db.refresh(sponsor)
    return sponsor_to_admin(sponsor)


@router.delete(
    "/v1/orgs/{slug}/admin/sponsors/{sponsor_slug}",
    response_model=SponsorAdminOut,
)
def archive_sponsor(
    slug: str,
    sponsor_slug: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SponsorAdminOut:
    """Archive a sponsor so it leaves public listings while the audit trail remains."""
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    sponsor = _get_sponsor_for_org(db, org, sponsor_slug)
    sponsor.status = "archived"
    touch(sponsor)
    write_audit(
        db,
        action="sponsor.archived",
        entity_type="sponsor",
        entity_id=str(sponsor.id),
        organization_id=org.id,
        actor_user_id=user.id,
    )
    db.commit()
    db.refresh(sponsor)
    return sponsor_to_admin(sponsor)
