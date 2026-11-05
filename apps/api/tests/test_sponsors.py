from __future__ import annotations

import io

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import AuditLog, Sponsor
from tests.helpers import auth_header, make_user


def test_public_sponsors_hide_drafts(client, db: Session) -> None:
    res = client.get("/v1/orgs/starks/sponsors")
    assert res.status_code == 200
    assert res.json() == []

    detail = client.get("/v1/orgs/starks/sponsors/hashtag-india-cary")
    assert detail.status_code == 404


def test_cross_club_sponsor_mutation_forbidden(client, db: Session, starks, steelers) -> None:
    _, starks_admin = make_user(db, email="s-admin@example.com", org=starks, role="admin")
    _, steelers_admin = make_user(
        db, email="e-admin@example.com", org=steelers, role="admin"
    )

    denied = client.patch(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary",
        headers=auth_header(steelers_admin),
        json={"tagline": "hacked"},
    )
    assert denied.status_code == 403

    ok = client.patch(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary",
        headers=auth_header(starks_admin),
        json={"tagline": "Updated founding sponsor"},
    )
    assert ok.status_code == 200
    assert ok.json()["tagline"] == "Updated founding sponsor"


def test_approve_publish_unpublish_and_audit(client, db: Session, starks) -> None:
    _, admin = make_user(db, email="publisher@example.com", org=starks, role="admin")
    headers = auth_header(admin)

    approve = client.post(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary/approve",
        headers=headers,
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    # Still not public until published
    assert client.get("/v1/orgs/starks/sponsors/hashtag-india-cary").status_code == 404

    publish = client.post(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary/publish",
        headers=headers,
    )
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"

    public = client.get("/v1/orgs/starks/sponsors/hashtag-india-cary")
    assert public.status_code == 200
    assert public.json()["name"] == "Hashtag India Cary"

    # Steelers public list still empty / no leakage
    assert client.get("/v1/orgs/steelers/sponsors").json() == []

    unpublish = client.post(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary/unpublish",
        headers=headers,
    )
    assert unpublish.status_code == 200
    assert unpublish.json()["status"] == "approved"

    actions = {
        row.action
        for row in db.scalars(
            select(AuditLog).where(AuditLog.organization_id == starks.id)
        ).all()
    }
    assert "sponsor.approved" in actions
    assert "sponsor.published" in actions
    assert "sponsor.unpublished" in actions


def test_upload_logo_local_storage(client, db: Session, starks, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MC360_LOCAL_STORAGE_DIR", str(tmp_path))
    from api.config import get_settings

    get_settings.cache_clear()

    _, admin = make_user(db, email="uploader@example.com", org=starks, role="admin")
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    res = client.post(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary/assets",
        headers=auth_header(admin),
        data={"asset_type": "logo"},
        files={"file": ("logo.png", io.BytesIO(png), "image/png")},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["asset_type"] == "logo"
    assert body["content_type"] == "image/png"
    assert str(starks.id) in body["storage_path"]

    sponsor = db.scalar(
        select(Sponsor).where(
            Sponsor.organization_id == starks.id,
            Sponsor.slug == "hashtag-india-cary",
        )
    )
    assert sponsor is not None
    assert sponsor.logo_path == body["storage_path"]


def test_publish_requires_approval(client, db: Session, starks) -> None:
    _, admin = make_user(db, email="early@example.com", org=starks, role="admin")
    res = client.post(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary/publish",
        headers=auth_header(admin),
    )
    assert res.status_code == 400


def test_upload_rejects_mismatched_signature(client, db: Session, starks) -> None:
    _, admin = make_user(db, email="badfile@example.com", org=starks, role="admin")
    res = client.post(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary/assets",
        headers=auth_header(admin),
        data={"asset_type": "logo"},
        files={"file": ("logo.png", io.BytesIO(b"not-a-png"), "image/png")},
    )
    assert res.status_code == 400
    assert "do not match" in res.json()["detail"]


def test_archive_hides_sponsor_and_cross_club_cannot_archive(
    client, db: Session, starks, steelers
) -> None:
    _, starks_admin = make_user(db, email="archiver@example.com", org=starks, role="admin")
    _, steelers_admin = make_user(db, email="other-archiver@example.com", org=steelers, role="admin")
    headers = auth_header(starks_admin)
    client.post("/v1/orgs/starks/admin/sponsors/hashtag-india-cary/approve", headers=headers)
    client.post("/v1/orgs/starks/admin/sponsors/hashtag-india-cary/publish", headers=headers)
    listed = client.get("/v1/orgs")
    starks_body = next(o for o in listed.json() if o["slug"] == "starks")
    assert starks_body["initial_sponsor"]["slug"] == "hashtag-india-cary"

    denied = client.delete(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary",
        headers=auth_header(steelers_admin),
    )
    assert denied.status_code == 403

    archived = client.delete(
        "/v1/orgs/starks/admin/sponsors/hashtag-india-cary",
        headers=headers,
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert client.get("/v1/orgs/starks/sponsors/hashtag-india-cary").status_code == 404
    hidden = next(o for o in client.get("/v1/orgs").json() if o["slug"] == "starks")
    assert hidden["initial_sponsor"] is None
