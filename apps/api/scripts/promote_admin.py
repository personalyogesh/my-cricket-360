#!/usr/bin/env python3
"""Promote a user (by email) to approved admin for a founding club.

Usage:
  cd apps/api
  uv run python scripts/promote_admin.py --email admin@starks.local --org starks
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sqlalchemy import select  # noqa: E402

from api.auth import ensure_profile  # noqa: E402
from api.db import SessionLocal  # noqa: E402
from api.models import Membership, Organization, utcnow  # noqa: E402
from api.seed import ensure_schema_and_seed  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--org", required=True, choices=["starks", "steelers"])
    parser.add_argument("--user-id", default=None, help="Optional stable UUID")
    args = parser.parse_args()

    ensure_schema_and_seed()
    db = SessionLocal()
    try:
        org = db.scalar(select(Organization).where(Organization.slug == args.org))
        if org is None:
            raise SystemExit(f"Organization {args.org} not found")
        user_id = uuid.UUID(args.user_id) if args.user_id else uuid.uuid4()
        # Reuse existing profile with same email when present
        from api.models import Profile

        existing = db.scalar(select(Profile).where(Profile.email == args.email))
        if existing is not None:
            user_id = existing.id
        ensure_profile(db, user_id, args.email)
        membership = db.scalar(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == org.id,
            )
        )
        if membership is None:
            membership = Membership(
                user_id=user_id,
                organization_id=org.id,
                role="admin",
                status="approved",
                requested_at=utcnow(),
                decided_at=utcnow(),
            )
            db.add(membership)
        else:
            membership.role = "admin"
            membership.status = "approved"
            membership.decided_at = utcnow()
        db.commit()
        print(f"Promoted {args.email} ({user_id}) to admin of {args.org}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
