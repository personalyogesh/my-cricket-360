from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    auth_mode: str | None = None
    storage_backend: str | None = None
    supabase_configured: bool | None = None
    supabase_host: str | None = None
    supabase_project_name: str | None = None
    database_driver: str | None = None
    # Never include credentials; name hint only (verify in Supabase Settings → Database)
    database_name_hint: str | None = None


class SponsorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    tagline: str | None = None
    description: str | None = None
    website_url: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    status: str
    sort_order: int = 0


class OrganizationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    short_name: str
    primary_domain: str
    theme: dict[str, Any] = Field(default_factory=dict)
    initial_sponsor: SponsorPublic | None = None


class HostResolveResponse(BaseModel):
    hostname: str
    kind: str
    organization: OrganizationPublic | None = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None = None
    display_name: str
    avatar_url: str | None = None
    phone: str | None = None


class ProfileUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=64)


class MembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    organization_slug: str
    organization_name: str
    user_id: uuid.UUID
    email: str | None = None
    display_name: str | None = None
    role: str
    status: str
    requested_at: datetime
    decided_at: datetime | None = None


class MeResponse(BaseModel):
    user: ProfileOut
    memberships: list[MembershipOut]
    approved_clubs: list[MembershipOut]


class MembershipRequestIn(BaseModel):
    organization_slug: str
    role: Literal["member"] = "member"


class MembershipDecisionIn(BaseModel):
    decision: Literal["approved", "rejected", "suspended"]
    role: Literal["member", "admin"] | None = None


class TeamPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    division: str | None = None
    season: str | None = None


class SponsorCreateIn(BaseModel):
    slug: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=255)
    tagline: str | None = None
    description: str | None = None
    website_url: str | None = None
    sort_order: int = 0


class SponsorUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tagline: str | None = None
    description: str | None = None
    website_url: str | None = None
    sort_order: int | None = None


class SponsorAdminOut(SponsorPublic):
    organization_id: uuid.UUID
    logo_path: str | None = None
    banner_path: str | None = None
    approved_at: datetime | None = None
    published_at: datetime | None = None


class SponsorAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sponsor_id: uuid.UUID
    organization_id: uuid.UUID
    asset_type: str
    storage_path: str
    content_type: str
    byte_size: int
    status: str
    url: str | None = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str | None
    meta: dict[str, Any]
    created_at: datetime


FixtureStatus = Literal[
    "draft",
    "scheduled",
    "postponed",
    "cancelled",
    "live",
    "completed",
]
ScheduleStatus = Literal["draft", "published"]


class FormatSpecOut(BaseModel):
    code: str
    name: str
    overs: int | None = None


class ScheduleIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    season: str = Field(min_length=1, max_length=64)
    competition: str = Field(min_length=1, max_length=128)
    format_code: str = Field(min_length=1, max_length=32)
    format_name: str | None = Field(default=None, max_length=128)
    overs: int | None = Field(default=None, ge=1, le=300)
    timezone: str = Field(min_length=1, max_length=64)
    status: ScheduleStatus = "draft"


class ScheduleUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    season: str | None = Field(default=None, min_length=1, max_length=64)
    competition: str | None = Field(default=None, min_length=1, max_length=128)
    format_code: str | None = Field(default=None, min_length=1, max_length=32)
    format_name: str | None = Field(default=None, max_length=128)
    overs: int | None = Field(default=None, ge=1, le=300)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    status: ScheduleStatus | None = None


class ScheduleOut(BaseModel):
    id: uuid.UUID
    name: str
    season: str
    competition: str
    format_code: str
    format_name: str
    overs: int | None
    timezone: str
    status: str


class ScheduleAdminOut(ScheduleOut):
    organization_id: uuid.UUID


class FixtureIn(BaseModel):
    schedule_id: uuid.UUID | None = None
    season: str = Field(min_length=1, max_length=64)
    competition: str = Field(min_length=1, max_length=128)
    home_team_id: uuid.UUID | None = None
    away_team_id: uuid.UUID | None = None
    home_team_name: str | None = Field(default=None, max_length=255)
    away_team_name: str | None = Field(default=None, max_length=255)
    venue: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    timezone: str = Field(min_length=1, max_length=64)
    format_code: str = Field(min_length=1, max_length=32)
    format_name: str | None = Field(default=None, max_length=128)
    overs: int | None = Field(default=None, ge=1, le=300)
    status: FixtureStatus = "draft"
    result_summary: str | None = Field(default=None, max_length=500)


class FixtureUpdateIn(BaseModel):
    schedule_id: uuid.UUID | None = None
    season: str | None = Field(default=None, min_length=1, max_length=64)
    competition: str | None = Field(default=None, min_length=1, max_length=128)
    home_team_id: uuid.UUID | None = None
    away_team_id: uuid.UUID | None = None
    home_team_name: str | None = Field(default=None, max_length=255)
    away_team_name: str | None = Field(default=None, max_length=255)
    venue: str | None = Field(default=None, min_length=1, max_length=255)
    starts_at: datetime | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    format_code: str | None = Field(default=None, min_length=1, max_length=32)
    format_name: str | None = Field(default=None, max_length=128)
    overs: int | None = Field(default=None, ge=1, le=300)
    status: FixtureStatus | None = None
    result_summary: str | None = Field(default=None, max_length=500)


class FixturePublic(BaseModel):
    id: uuid.UUID
    schedule_id: uuid.UUID | None
    season: str
    competition: str
    home_team_id: uuid.UUID | None
    away_team_id: uuid.UUID | None
    home_team_name: str
    away_team_name: str
    venue: str
    starts_at: datetime
    timezone: str
    format_code: str
    format_name: str
    overs: int | None
    status: str
    result_summary: str | None


class FixtureAdminOut(FixturePublic):
    organization_id: uuid.UUID


class FixturePage(BaseModel):
    items: list[FixturePublic]
    total: int
    limit: int
    offset: int


class FixtureAdminPage(BaseModel):
    items: list[FixtureAdminOut]
    total: int
    limit: int
    offset: int


class SchedulePage(BaseModel):
    items: list[ScheduleOut]
    total: int
    limit: int
    offset: int


class ScheduleAdminPage(BaseModel):
    items: list[ScheduleAdminOut]
    total: int
    limit: int
    offset: int


class DevTokenRequest(BaseModel):
    user_id: uuid.UUID | None = None
    email: str = "dev@example.com"
    display_name: str = "Dev User"


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: ProfileOut
    note: str
