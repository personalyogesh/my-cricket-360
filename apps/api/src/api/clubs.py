"""Server-side founding club catalog and hostname allowlist.

Mirrors apps/web allowlist semantics. Unknown hosts never resolve to a club.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ClubSponsorSeed:
    slug: str
    name: str
    tagline: str
    website_url: str


@dataclass(frozen=True, slots=True)
class ClubConfig:
    slug: str
    organization_id: str
    name: str
    short_name: str
    primary_domain: str
    production_hosts: tuple[str, ...]
    initial_sponsor: ClubSponsorSeed


STARKS: Final = ClubConfig(
    slug="starks",
    organization_id="00000000-0000-4000-8000-000000000001",
    name="Starks Cricket",
    short_name="Starks",
    primary_domain="starksgroup.org",
    production_hosts=("starksgroup.org", "www.starksgroup.org"),
    initial_sponsor=ClubSponsorSeed(
        slug="hashtag-india-cary",
        name="Hashtag India Cary",
        tagline="Proud founding sponsor of Starks Cricket",
        website_url="https://hashtagindiacary.com",
    ),
)

STEELERS: Final = ClubConfig(
    slug="steelers",
    organization_id="00000000-0000-4000-8000-000000000002",
    name="CGI Steelers Cricket",
    short_name="Steelers",
    primary_domain="cgisteelerscricket.org",
    production_hosts=("cgisteelerscricket.org", "www.cgisteelerscricket.org"),
    initial_sponsor=ClubSponsorSeed(
        slug="cgi",
        name="CGI",
        tagline="Proud founding sponsor of CGI Steelers Cricket",
        website_url="https://www.cgi.com",
    ),
)

CLUBS_BY_SLUG: Final[dict[str, ClubConfig]] = {
    STARKS.slug: STARKS,
    STEELERS.slug: STEELERS,
}

LOCAL_HOST_TO_SLUG: Final[dict[str, str]] = {
    "starks.localhost": "starks",
    "www.starks.localhost": "starks",
    "steelers.localhost": "steelers",
    "www.steelers.localhost": "steelers",
}

PLATFORM_HOSTS: Final[set[str]] = {
    "localhost",
    "127.0.0.1",
    "mycricket360.localhost",
    "www.mycricket360.localhost",
}


def build_host_allowlist() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for club in CLUBS_BY_SLUG.values():
        for host in club.production_hosts:
            mapping[host.lower()] = club.slug
    for host, slug in LOCAL_HOST_TO_SLUG.items():
        mapping[host.lower()] = slug
    return mapping


HOST_ALLOWLIST: Final[dict[str, str]] = build_host_allowlist()


def normalize_host(raw_host: str | None) -> str:
    if not raw_host:
        return ""
    host = raw_host.strip().lower()
    if host.startswith("["):
        end = host.find("]")
        if end != -1:
            ipv6 = host[1:end]
            return ipv6
    colon = host.rfind(":")
    if colon != -1 and host.find(":") == colon:
        maybe_port = host[colon + 1 :]
        if maybe_port.isdigit():
            host = host[:colon]
    if not host or " " in host or "/" in host or "?" in host:
        return ""
    return host


def resolve_club_slug_from_host(raw_host: str | None) -> str | None:
    """Return club slug only for allowlisted hosts; never guess."""
    hostname = normalize_host(raw_host)
    if not hostname or hostname in PLATFORM_HOSTS:
        return None
    return HOST_ALLOWLIST.get(hostname)


def get_club(slug: str) -> ClubConfig | None:
    return CLUBS_BY_SLUG.get(slug)
