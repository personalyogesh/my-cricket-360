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


def test_member_cannot_decide_and_cross_club_decision_is_forbidden(
    client, db: Session, starks, steelers
) -> None:
    _, starks_admin = make_user(db, email="decider@example.com", org=starks, role="admin")
    _, starks_member = make_user(db, email="member@example.com", org=starks, role="member")
    player_id, player_token = make_user(db, email="applicant@example.com")

    requested = client.post(
        "/v1/me/memberships",
        headers=auth_header(player_token),
        json={"organization_slug": "starks"},
    )
    assert requested.status_code == 201
    membership_id = requested.json()["id"]

    denied_member = client.post(
        f"/v1/orgs/starks/memberships/{membership_id}/decision",
        headers=auth_header(starks_member),
        json={"decision": "approved", "role": "admin"},
    )
    assert denied_member.status_code == 403

    steelers_row = client.post(
        "/v1/me/memberships",
        headers=auth_header(player_token),
        json={"organization_slug": "steelers"},
    )
    assert steelers_row.status_code == 201
    cross = client.post(
        f"/v1/orgs/steelers/memberships/{steelers_row.json()['id']}/decision",
        headers=auth_header(starks_admin),
        json={"decision": "approved"},
    )
    assert cross.status_code == 403

    mismatched = client.post(
        f"/v1/orgs/starks/memberships/{steelers_row.json()['id']}/decision",
        headers=auth_header(starks_admin),
        json={"decision": "approved"},
    )
    assert mismatched.status_code == 404

    role_on_reject = client.post(
        f"/v1/orgs/starks/memberships/{membership_id}/decision",
        headers=auth_header(starks_admin),
        json={"decision": "rejected", "role": "admin"},
    )
    assert role_on_reject.status_code == 400

    suspended = client.post(
        f"/v1/orgs/starks/memberships/{membership_id}/decision",
        headers=auth_header(starks_admin),
        json={"decision": "suspended"},
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"
    assert suspended.json()["role"] == "member"

    blocked_admin = client.get(
        "/v1/orgs/starks/admin/sponsors",
        headers=auth_header(player_token),
    )
    assert blocked_admin.status_code == 403

    again = client.post(
        "/v1/me/memberships",
        headers=auth_header(player_token),
        json={"organization_slug": "starks"},
    )
    assert again.status_code == 201
    assert again.json()["status"] == "pending"
    assert again.json()["role"] == "member"
    assert player_id is not None


def test_profile_update(client, db: Session) -> None:
    _, token = make_user(db, email="profile@example.com")
    updated = client.patch(
        "/v1/me",
        headers=auth_header(token),
        json={"display_name": "Updated Player", "phone": "919-555-0100"},
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Updated Player"
    assert updated.json()["phone"] == "919-555-0100"
    assert updated.json()["email"] == "profile@example.com"

    empty = client.patch("/v1/me", headers=auth_header(token), json={})
    assert empty.status_code == 400
