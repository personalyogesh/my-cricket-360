from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import Membership
from tests.helpers import auth_header, make_user


def test_me_requires_auth(client) -> None:
    assert client.get("/v1/me").status_code == 401


def test_membership_request_approve_and_self_approval_blocked(
    client, db: Session, starks
) -> None:
    _, admin_token = make_user(db, email="starks-admin@example.com", org=starks, role="admin")
    admin_profile = client.get("/v1/me", headers=auth_header(admin_token)).json()
    admin_id = uuid.UUID(admin_profile["user"]["id"])

    _, member_token = make_user(db, email="player@example.com")

    req = client.post(
        "/v1/me/memberships",
        headers=auth_header(member_token),
        json={"organization_slug": "starks"},
    )
    assert req.status_code == 201
    membership_id = req.json()["id"]
    assert req.json()["status"] == "pending"

    # Self-approval / self privilege change is always forbidden
    own = db.scalar(
        select(Membership).where(
            Membership.user_id == admin_id,
            Membership.organization_id == starks.id,
        )
    )
    assert own is not None
    blocked = client.post(
        f"/v1/orgs/starks/memberships/{own.id}/decision",
        headers=auth_header(admin_token),
        json={"decision": "approved", "role": "admin"},
    )
    assert blocked.status_code == 403
    assert "own membership" in blocked.json()["detail"].lower()

    approved = client.post(
        f"/v1/orgs/starks/memberships/{membership_id}/decision",
        headers=auth_header(admin_token),
        json={"decision": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    clubs = client.get("/v1/me/clubs", headers=auth_header(member_token))
    assert clubs.status_code == 200
    assert any(c["organization_slug"] == "starks" for c in clubs.json())


def test_cross_club_admin_cannot_list_other_memberships(
    client, db: Session, starks, steelers
) -> None:
    _, starks_admin = make_user(db, email="s-admin@example.com", org=starks, role="admin")
    _, steelers_admin = make_user(
        db, email="e-admin@example.com", org=steelers, role="admin"
    )

    denied = client.get(
        "/v1/orgs/steelers/memberships",
        headers=auth_header(starks_admin),
    )
    assert denied.status_code == 403

    allowed = client.get(
        "/v1/orgs/steelers/memberships",
        headers=auth_header(steelers_admin),
    )
    assert allowed.status_code == 200
