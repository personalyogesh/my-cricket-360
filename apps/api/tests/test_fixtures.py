from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import AuditLog, Fixture, Team
from tests.helpers import auth_header, make_user


def _team(db: Session, org_id, name: str) -> Team:
    team = Team(organization_id=org_id, name=name, is_public=True)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def _payload(**overrides):
    body = {
        "season": "2026",
        "competition": "Sunday League",
        "home_team_name": "Starks First XI",
        "away_team_name": "Visitors",
        "venue": "Starks Ground",
        "starts_at": "2026-06-14T14:00:00-04:00",
        "timezone": "America/New_York",
        "format_code": "t20",
        "status": "scheduled",
    }
    body.update(overrides)
    return body


def test_builtin_formats_and_configurable_overs(client) -> None:
    catalog = client.get("/v1/fixture-formats")
    assert catalog.status_code == 200
    by_code = {row["code"]: row for row in catalog.json()}
    assert by_code["t20"]["overs"] == 20
    assert by_code["premier_40"] == {"code": "premier_40", "name": "Premier League", "overs": 40}
    assert by_code["ht"]["name"] == "HT"
    assert by_code["ht"]["overs"] is None


def test_admin_crud_hides_drafts_and_does_not_invent_results(client, db: Session, starks) -> None:
    _, token = make_user(db, email="fix-admin@example.com", org=starks, role="admin")
    headers = auth_header(token)
    home = _team(db, starks.id, "Starks First XI")

    created = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=headers,
        json=_payload(
            home_team_id=str(home.id),
            home_team_name=None,
            status="draft",
            format_code="ht",
        ),
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["home_team_name"] == "Starks First XI"
    assert body["format_name"] == "HT"
    assert body["overs"] is None
    assert body["result_summary"] is None
    fixture_id = body["id"]

    hidden = client.get(f"/v1/orgs/starks/fixtures/{fixture_id}")
    assert hidden.status_code == 404
    public = client.get("/v1/orgs/starks/fixtures")
    assert public.json()["total"] == 0

    completed = client.patch(
        f"/v1/orgs/starks/admin/fixtures/{fixture_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["result_summary"] is None

    noted = client.patch(
        f"/v1/orgs/starks/admin/fixtures/{fixture_id}",
        headers=headers,
        json={"result_summary": "Starks won by 4 wickets"},
    )
    assert noted.json()["result_summary"] == "Starks won by 4 wickets"

    visible = client.get("/v1/orgs/starks/fixtures", params={"when": "completed"})
    assert visible.json()["total"] == 1
    assert visible.json()["items"][0]["result_summary"] == "Starks won by 4 wickets"

    audit = db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == starks.id,
            AuditLog.entity_type == "fixture",
        )
    ).all()
    assert {row.action for row in audit} >= {"fixture.created", "fixture.updated"}


def test_patch_without_start_time_keeps_the_original_instant(client, db: Session, starks) -> None:
    _, token = make_user(db, email="keep-time@example.com", org=starks, role="admin")
    headers = auth_header(token)
    created = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=headers,
        json=_payload(starts_at="2026-11-01T06:30:00Z", timezone="America/New_York"),
    )
    assert created.status_code == 201, created.text
    original = created.json()["starts_at"]
    fixture_id = created.json()["id"]

    patched = client.patch(
        f"/v1/orgs/starks/admin/fixtures/{fixture_id}",
        headers=headers,
        json={"result_summary": "Recorded by the club", "venue": "Starks Ground"},
    )
    assert patched.status_code == 200
    assert patched.json()["starts_at"] == original
    assert patched.json()["timezone"] == "America/New_York"
    assert patched.json()["result_summary"] == "Recorded by the club"

    moved = client.patch(
        f"/v1/orgs/starks/admin/fixtures/{fixture_id}",
        headers=headers,
        json={"starts_at": "2026-06-14T18:00:00Z", "timezone": "America/New_York"},
    )
    assert moved.status_code == 200
    assert moved.json()["starts_at"] != original
    assert moved.json()["starts_at"].startswith("2026-06-14T18:00:00")
    assert moved.json()["starts_at"].endswith("+00:00") or moved.json()["starts_at"].endswith("Z")


def test_cross_club_admin_cannot_mutate_or_list(client, db: Session, starks, steelers) -> None:
    _, steelers_admin = make_user(db, email="steel-admin@example.com", org=steelers, role="admin")
    _, member = make_user(db, email="member@example.com", org=starks, role="member")
    home = _team(db, starks.id, "Starks")
    away = _team(db, steelers.id, "Steelers")

    denied = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=auth_header(steelers_admin),
        json=_payload(),
    )
    assert denied.status_code == 403

    member_denied = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=auth_header(member),
        json=_payload(),
    )
    assert member_denied.status_code == 403

    anon = client.get("/v1/orgs/starks/admin/fixtures")
    assert anon.status_code == 401

    foreign_team = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=auth_header(make_user(db, email="s-admin2@example.com", org=starks, role="admin")[1]),
        json=_payload(home_team_id=str(home.id), away_team_id=str(away.id)),
    )
    assert foreign_team.status_code == 400

    other = client.get("/v1/orgs/steelers/fixtures")
    assert other.json()["items"] == []
    assert db.scalar(select(Fixture).where(Fixture.organization_id == steelers.id)) is None


def test_filters_pagination_formats_and_schedules(client, db: Session, starks) -> None:
    _, token = make_user(db, email="sched@example.com", org=starks, role="admin")
    headers = auth_header(token)
    home = _team(db, starks.id, "Starks First XI")

    schedule = client.post(
        "/v1/orgs/starks/admin/schedules",
        headers=headers,
        json={
            "name": "Summer Sundays",
            "season": "2026",
            "competition": "Sunday League",
            "format_code": "premier_40",
            "timezone": "America/New_York",
            "status": "published",
        },
    )
    assert schedule.status_code == 201, schedule.text
    assert schedule.json()["overs"] == 40
    schedule_id = schedule.json()["id"]

    draft_schedule = client.post(
        "/v1/orgs/starks/admin/schedules",
        headers=headers,
        json={
            "name": "Internal nets",
            "season": "2026",
            "competition": "Nets",
            "format_code": "custom_8",
            "format_name": "8-over pairs",
            "overs": 8,
            "timezone": "America/New_York",
            "status": "draft",
        },
    )
    assert draft_schedule.status_code == 201

    public_schedules = client.get("/v1/orgs/starks/schedules")
    assert public_schedules.json()["total"] == 1
    assert public_schedules.json()["items"][0]["name"] == "Summer Sundays"
    hidden = client.get(f"/v1/orgs/starks/schedules/{draft_schedule.json()['id']}")
    assert hidden.status_code == 404

    first = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=headers,
        json=_payload(
            schedule_id=schedule_id,
            home_team_id=str(home.id),
            format_code="premier_40",
            starts_at="2026-06-14T14:00:00-04:00",
        ),
    )
    second = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=headers,
        json=_payload(
            home_team_id=str(home.id),
            away_team_name="Night XI",
            format_code="t20",
            starts_at="2026-07-02T18:30:00-04:00",
        ),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["overs"] == 40
    assert second.json()["overs"] == 20

    premier = client.get(
        "/v1/orgs/starks/fixtures",
        params={"format_code": "premier_40", "team_id": str(home.id), "date_from": "2026-06-01", "date_to": "2026-06-30"},
    )
    assert premier.json()["total"] == 1
    assert premier.json()["items"][0]["format_code"] == "premier_40"

    page = client.get("/v1/orgs/starks/fixtures", params={"limit": 1, "offset": 1, "when": "upcoming"})
    assert page.json()["total"] == 2
    assert len(page.json()["items"]) == 1

    bad_zone = client.post(
        "/v1/orgs/starks/admin/fixtures",
        headers=headers,
        json=_payload(timezone="Not/AZone"),
    )
    assert bad_zone.status_code == 422

    missing_name = client.post(
        "/v1/orgs/starks/admin/schedules",
        headers=headers,
        json={
            "name": "Mystery",
            "season": "2026",
            "competition": "Other",
            "format_code": "club_cup",
            "timezone": "America/New_York",
        },
    )
    assert missing_name.status_code == 422

    removed = client.delete(
        f"/v1/orgs/starks/admin/fixtures/{second.json()['id']}",
        headers=headers,
    )
    assert removed.status_code == 204
    assert client.get(f"/v1/orgs/starks/fixtures/{second.json()['id']}").status_code == 404
    created_audit = db.scalar(
        select(AuditLog).where(
            AuditLog.action == "schedule.created",
            AuditLog.organization_id == starks.id,
        )
    )
    assert created_audit is not None
    assert uuid.UUID(first.json()["id"])
