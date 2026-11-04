from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from api.auth import create_dev_access_token, ensure_profile
from api.models import Membership, Organization, utcnow


def make_user(
    db: Session,
    *,
    email: str,
    org: Organization | None = None,
    role: str = "member",
    status: str = "approved",
) -> tuple[uuid.UUID, str]:
    user_id = uuid.uuid4()
    ensure_profile(db, user_id, email)
    if org is not None:
        db.add(
            Membership(
                user_id=user_id,
                organization_id=org.id,
                role=role,
                status=status,
                requested_at=utcnow(),
                decided_at=utcnow() if status == "approved" else None,
            )
        )
    db.commit()
    token = create_dev_access_token(user_id=user_id, email=email)
    return user_id, token


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
