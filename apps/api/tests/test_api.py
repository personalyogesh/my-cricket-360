from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "my-cricket-360-api"


def test_list_orgs_includes_founding_clubs_and_sponsors() -> None:
    res = client.get("/v1/orgs")
    assert res.status_code == 200
    orgs = {o["slug"]: o for o in res.json()}
    assert set(orgs) == {"starks", "steelers"}
    assert orgs["starks"]["initial_sponsor"]["name"] == "Hashtag India Cary"
    assert orgs["steelers"]["initial_sponsor"]["name"] == "CGI"
    assert orgs["starks"]["id"] != orgs["steelers"]["id"]


def test_resolve_host_club_and_unknown() -> None:
    ok = client.get("/v1/resolve-host", params={"host": "www.starksgroup.org"})
    assert ok.status_code == 200
    assert ok.json()["kind"] == "club"
    assert ok.json()["organization"]["slug"] == "starks"

    bad = client.get("/v1/resolve-host", params={"host": "not-allowlisted.test"})
    assert bad.status_code == 200
    assert bad.json()["kind"] == "unknown"
    assert bad.json()["organization"] is None
