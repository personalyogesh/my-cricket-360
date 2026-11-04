from api.clubs import (
    HOST_ALLOWLIST,
    normalize_host,
    resolve_club_slug_from_host,
)


def test_normalize_host_strips_port_and_case() -> None:
    assert normalize_host("WWW.StarksGroup.org:443") == "www.starksgroup.org"
    assert normalize_host("steelers.localhost:8400") == "steelers.localhost"


def test_founding_hosts_resolve() -> None:
    assert resolve_club_slug_from_host("starksgroup.org") == "starks"
    assert resolve_club_slug_from_host("www.starksgroup.org") == "starks"
    assert resolve_club_slug_from_host("cgisteelerscricket.org") == "steelers"
    assert resolve_club_slug_from_host("www.cgisteelerscricket.org") == "steelers"
    assert resolve_club_slug_from_host("starks.localhost:43123") == "starks"


def test_unknown_host_never_resolves_to_club() -> None:
    assert resolve_club_slug_from_host("evil.starksgroup.org") is None
    assert resolve_club_slug_from_host("cgi.com") is None
    assert resolve_club_slug_from_host("localhost") is None
    assert resolve_club_slug_from_host("") is None


def test_allowlist_has_apex_and_www() -> None:
    assert HOST_ALLOWLIST["starksgroup.org"] == "starks"
    assert HOST_ALLOWLIST["www.starksgroup.org"] == "starks"
    assert HOST_ALLOWLIST["cgisteelerscricket.org"] == "steelers"
    assert HOST_ALLOWLIST["www.cgisteelerscricket.org"] == "steelers"
