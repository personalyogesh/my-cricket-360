from __future__ import annotations


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
