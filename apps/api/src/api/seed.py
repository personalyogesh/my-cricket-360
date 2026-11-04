"""Idempotent founding-club and sponsor seeds. Safe to rerun."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.clubs import CLUBS_BY_SLUG
from api.db import SessionLocal, engine
from api.models import Base, Organization, OrganizationDomain, Sponsor

STARKS_THEME: dict[str, Any] = {
    "primary": "#0B3D2E",
    "secondary": "#1A5C45",
    "background": "#F3F7F4",
    "foreground": "#10231C",
    "muted": "#D7E5DD",
    "accent": "#C4A35A",
}

STEELERS_THEME: dict[str, Any] = {
    "primary": "#1B2A4A",
    "secondary": "#2E4570",
    "background": "#F2F4F8",
    "foreground": "#121826",
    "muted": "#D8DEEA",
    "accent": "#B33A3A",
}

THEMES = {"starks": STARKS_THEME, "steelers": STEELERS_THEME}


def _upsert_organization(db: Session, slug: str) -> Organization:
    club = CLUBS_BY_SLUG[slug]
    org_id = uuid.UUID(club.organization_id)
    org = db.get(Organization, org_id)
    if org is None:
        existing = db.scalar(select(Organization).where(Organization.slug == slug))
        org = existing
    if org is None:
        org = Organization(id=org_id, slug=slug)
        db.add(org)

    org.id = org_id
    org.slug = slug
    org.name = club.name
    org.short_name = club.short_name
    org.status = "active"
    org.primary_domain = club.primary_domain
    org.theme = THEMES[slug]
    org.settings = {"founding": True}
    org.subscription_status = "founding"
    db.flush()
    return org


def _upsert_domains(db: Session, org: Organization) -> None:
    club = CLUBS_BY_SLUG[org.slug]
    desired: list[tuple[str, str, bool]] = []
    for host in club.production_hosts:
        desired.append((host, "production", host == club.primary_domain))
    desired.append((f"{org.slug}.localhost", "local", False))
    desired.append((f"www.{org.slug}.localhost", "local", False))

    existing = {
        d.hostname: d
        for d in db.scalars(
            select(OrganizationDomain).where(OrganizationDomain.organization_id == org.id)
        )
    }
    for hostname, environment, is_primary in desired:
        row = existing.get(hostname)
        if row is None:
            row = OrganizationDomain(
                organization_id=org.id,
                hostname=hostname,
                environment=environment,
                is_primary=is_primary,
            )
            db.add(row)
        else:
            row.environment = environment
            row.is_primary = is_primary
            row.organization_id = org.id


def _upsert_founding_sponsor(db: Session, org: Organization) -> Sponsor:
    """Seed founding sponsors as draft — no fabricated logos."""
    club = CLUBS_BY_SLUG[org.slug]
    seed = club.initial_sponsor
    sponsor = db.scalar(
        select(Sponsor).where(
            Sponsor.organization_id == org.id,
            Sponsor.slug == seed.slug,
        )
    )
    if sponsor is None:
        sponsor = Sponsor(
            organization_id=org.id,
            slug=seed.slug,
            name=seed.name,
            status="draft",
        )
        db.add(sponsor)

    sponsor.name = seed.name
    sponsor.tagline = seed.tagline
    sponsor.description = (
        f"{seed.name} is the founding sponsor profile for {club.name}. "
        "Marked draft until assets and details are verified by club admins."
    )
    sponsor.website_url = seed.website_url
    # Do not invent logo/banner paths
    if sponsor.status not in {"published", "approved", "archived", "rejected"}:
        sponsor.status = "draft"
    sponsor.sort_order = 0
    return sponsor


def seed_founding_data(db: Session) -> dict[str, str]:
    """Upsert founding orgs, domains, and draft sponsors. Returns org slug → id."""
    result: dict[str, str] = {}
    for slug in ("starks", "steelers"):
        org = _upsert_organization(db, slug)
        _upsert_domains(db, org)
        _upsert_founding_sponsor(db, org)
        result[slug] = str(org.id)
    db.commit()
    return result


def ensure_schema_and_seed(db: Session | None = None) -> dict[str, str]:
    Base.metadata.create_all(bind=engine)
    own = db is None
    session = db or SessionLocal()
    try:
        return seed_founding_data(session)
    finally:
        if own:
            session.close()


def main() -> None:
    mapping = ensure_schema_and_seed()
    print("Seeded organizations:", mapping)


if __name__ == "__main__":
    main()
