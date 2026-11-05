from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from api.models import AuditLog, Membership, Organization, Sponsor, utcnow
from api.schemas import MembershipOut, OrganizationPublic, SponsorAdminOut, SponsorPublic
from api.storage import StorageService


def write_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    organization_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    row = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        meta=meta or {},
    )
    db.add(row)
    db.flush()
    return row


def sponsor_to_public(sponsor: Sponsor, storage: StorageService | None = None) -> SponsorPublic:
    storage = storage or StorageService()
    return SponsorPublic(
        id=sponsor.id,
        slug=sponsor.slug,
        name=sponsor.name,
        tagline=sponsor.tagline,
        description=sponsor.description,
        website_url=sponsor.website_url,
        logo_url=storage.public_url(sponsor.logo_path),
        banner_url=storage.public_url(sponsor.banner_path),
        status=sponsor.status,
        sort_order=sponsor.sort_order,
    )


def sponsor_to_admin(sponsor: Sponsor, storage: StorageService | None = None) -> SponsorAdminOut:
    base = sponsor_to_public(sponsor, storage)
    return SponsorAdminOut(
        **base.model_dump(),
        organization_id=sponsor.organization_id,
        logo_path=sponsor.logo_path,
        banner_path=sponsor.banner_path,
        approved_at=sponsor.approved_at,
        published_at=sponsor.published_at,
    )


def org_to_public(
    org: Organization,
    *,
    founding_sponsor: Sponsor | None = None,
    storage: StorageService | None = None,
) -> OrganizationPublic:
    return OrganizationPublic(
        id=org.id,
        slug=org.slug,
        name=org.name,
        short_name=org.short_name,
        primary_domain=org.primary_domain,
        theme=org.theme or {},
        initial_sponsor=sponsor_to_public(founding_sponsor, storage) if founding_sponsor else None,
    )


def membership_to_out(membership: Membership, org: Organization) -> MembershipOut:
    profile = membership.user
    return MembershipOut(
        id=membership.id,
        organization_id=membership.organization_id,
        organization_slug=org.slug,
        organization_name=org.name,
        user_id=membership.user_id,
        email=profile.email if profile is not None else None,
        display_name=profile.display_name if profile is not None else None,
        role=membership.role,
        status=membership.status,
        requested_at=membership.requested_at,
        decided_at=membership.decided_at,
    )


def touch(sponsor: Sponsor) -> None:
    sponsor.updated_at = utcnow()
