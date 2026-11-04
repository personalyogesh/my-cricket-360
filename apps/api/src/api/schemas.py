from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class SponsorPublic(BaseModel):
    slug: str
    name: str
    tagline: str
    website_url: str


class OrganizationPublic(BaseModel):
    id: str
    slug: str
    name: str
    short_name: str
    primary_domain: str
    initial_sponsor: SponsorPublic


class HostResolveResponse(BaseModel):
    hostname: str
    kind: str
    organization: OrganizationPublic | None = None
