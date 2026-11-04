from __future__ import annotations

from api.models import Team


def test_health(client) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "my-cricket-360-api"
    assert body["auth_mode"] == "dev"


def test_resolve_host_club_and_unknown(client) -> None:
    ok = client.get("/v1/resolve-host", params={"host": "www.starksgroup.org"})
    assert ok.status_code == 200
    assert ok.json()["kind"] == "club"
    assert ok.json()["organization"]["slug"] == "starks"

    bad = client.get("/v1/resolve-host", params={"host": "not-allowlisted.test"})
    assert bad.status_code == 200
    assert bad.json()["kind"] == "unknown"
    assert bad.json()["organization"] is None


def test_dev_token_endpoint(client) -> None:
    res = client.post(
        "/v1/auth/dev-token",
        json={"email": "dev@example.com", "display_name": "Dev"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    me = client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "dev@example.com"

    again = client.post(
        "/v1/auth/dev-token",
        json={"email": "dev@example.com", "display_name": "Dev"},
    )
    assert again.status_code == 200
    assert again.json()["user"]["id"] == me.json()["user"]["id"]


def test_public_teams_are_club_scoped(client, db, starks, steelers) -> None:
    db.add(Team(organization_id=starks.id, name="Starks First XI", division="Premier", is_public=True))
    db.add(Team(organization_id=starks.id, name="Starks Nets", is_public=False))
    db.add(Team(organization_id=steelers.id, name="Steelers Sunday", is_public=True))
    db.commit()

    starks_teams = client.get("/v1/orgs/starks/teams")
    assert starks_teams.status_code == 200
    names = [row["name"] for row in starks_teams.json()]
    assert names == ["Starks First XI"]
    assert "division" in starks_teams.json()[0]
    assert "Steelers Sunday" not in names

    assert client.get("/v1/orgs/missing/teams").status_code == 404
