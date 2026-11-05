"""Organization-scoped fixtures and match schedules."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from api.auth import AuthUser, get_current_user, require_org_admin
from api.cricket_formats import BUILTIN_FORMATS, resolve_format
from api.db import get_db
from api.models import (
    PUBLIC_FIXTURE_STATUSES,
    Fixture,
    Organization,
    Schedule,
    Team,
    utcnow,
)
from api.schemas import (
    FixtureAdminOut,
    FixtureAdminPage,
    FixtureIn,
    FixturePage,
    FixturePublic,
    FixtureUpdateIn,
    FormatSpecOut,
    ScheduleAdminOut,
    ScheduleAdminPage,
    ScheduleIn,
    ScheduleOut,
    SchedulePage,
    ScheduleUpdateIn,
)
from api.services import write_audit

router = APIRouter(tags=["fixtures"])

UPCOMING_STATUSES = ("scheduled", "postponed", "live")


def _get_org(db: Session, slug: str) -> Organization:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def _require_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Unknown timezone") from exc
    return value


def _require_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise HTTPException(status_code=422, detail="starts_at must include a timezone offset")
    return value


def _clean_result(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _team_side(
    db: Session,
    org: Organization,
    team_id: uuid.UUID | None,
    name: str | None,
    *,
    label: str,
) -> tuple[uuid.UUID | None, str]:
    if team_id is not None:
        team = db.get(Team, team_id)
        if team is None or team.organization_id != org.id:
            raise HTTPException(status_code=400, detail=f"{label} team is not in this club")
        display = (name or "").strip() or team.name
        return team.id, display
    display = (name or "").strip()
    if not display:
        raise HTTPException(
            status_code=422,
            detail=f"{label} team name is required when no club team is selected",
        )
    return None, display


def _schedule_for_org(db: Session, org: Organization, schedule_id: uuid.UUID) -> Schedule:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None or schedule.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


def _fixture_for_org(db: Session, org: Organization, fixture_id: uuid.UUID) -> Fixture:
    fixture = db.get(Fixture, fixture_id)
    if fixture is None or fixture.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return fixture


def _schedule_out(row: Schedule) -> ScheduleOut:
    return ScheduleOut(
        id=row.id,
        name=row.name,
        season=row.season,
        competition=row.competition,
        format_code=row.format_code,
        format_name=row.format_name,
        overs=row.overs,
        timezone=row.timezone,
        status=row.status,
    )


def _schedule_admin(row: Schedule) -> ScheduleAdminOut:
    base = _schedule_out(row)
    return ScheduleAdminOut(**base.model_dump(), organization_id=row.organization_id)


def _as_utc(value: datetime) -> datetime:
    """SQLite drops tzinfo; stored fixture instants are UTC either way."""
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _fixture_public(row: Fixture) -> FixturePublic:
    return FixturePublic(
        id=row.id,
        schedule_id=row.schedule_id,
        season=row.season,
        competition=row.competition,
        home_team_id=row.home_team_id,
        away_team_id=row.away_team_id,
        home_team_name=row.home_team_name,
        away_team_name=row.away_team_name,
        venue=row.venue,
        starts_at=_as_utc(row.starts_at),
        timezone=row.timezone,
        format_code=row.format_code,
        format_name=row.format_name,
        overs=row.overs,
        status=row.status,
        result_summary=row.result_summary,
    )


def _fixture_admin(row: Fixture) -> FixtureAdminOut:
    base = _fixture_public(row)
    return FixtureAdminOut(**base.model_dump(), organization_id=row.organization_id)


def _apply_fixture_filters(
    stmt,
    *,
    team_id: uuid.UUID | None,
    team: str | None,
    format_code: str | None,
    date_from: date | None,
    date_to: date | None,
    status: str | None,
    when: str | None,
    public_only: bool,
):
    if public_only:
        stmt = stmt.where(Fixture.status.in_(PUBLIC_FIXTURE_STATUSES))
    if status:
        stmt = stmt.where(Fixture.status == status)
    if when == "upcoming":
        stmt = stmt.where(Fixture.status.in_(UPCOMING_STATUSES))
    elif when == "completed":
        stmt = stmt.where(Fixture.status == "completed")
    elif when is not None:
        raise HTTPException(status_code=422, detail="when must be upcoming or completed")
    if team_id is not None:
        stmt = stmt.where(
            or_(Fixture.home_team_id == team_id, Fixture.away_team_id == team_id)
        )
    if team:
        like = f"%{team.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Fixture.home_team_name).like(like),
                func.lower(Fixture.away_team_name).like(like),
            )
        )
    if format_code:
        stmt = stmt.where(Fixture.format_code == format_code.strip().lower())
    if date_from is not None:
        start = datetime.combine(date_from, time.min, tzinfo=UTC)
        stmt = stmt.where(Fixture.starts_at >= start)
    if date_to is not None:
        end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
        stmt = stmt.where(Fixture.starts_at < end)
    return stmt


@router.get("/v1/fixture-formats", response_model=list[FormatSpecOut])
def list_fixture_formats() -> list[FormatSpecOut]:
    return [FormatSpecOut(code=spec.code, name=spec.name, overs=spec.overs) for spec in BUILTIN_FORMATS]


@router.get("/v1/orgs/{slug}/schedules", response_model=SchedulePage)
def list_public_schedules(
    slug: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SchedulePage:
    org = _get_org(db, slug)
    stmt = select(Schedule).where(
        Schedule.organization_id == org.id,
        Schedule.status == "published",
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Schedule.season.desc(), Schedule.name.asc()).limit(limit).offset(offset)
    ).all()
    return SchedulePage(
        items=[_schedule_out(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/v1/orgs/{slug}/schedules/{schedule_id}", response_model=ScheduleOut)
def get_public_schedule(
    slug: str, schedule_id: uuid.UUID, db: Session = Depends(get_db)
) -> ScheduleOut:
    org = _get_org(db, slug)
    schedule = _schedule_for_org(db, org, schedule_id)
    if schedule.status != "published":
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _schedule_out(schedule)


@router.get("/v1/orgs/{slug}/fixtures", response_model=FixturePage)
def list_public_fixtures(
    slug: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    team_id: uuid.UUID | None = None,
    team: str | None = None,
    format_code: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    when: str | None = None,
    db: Session = Depends(get_db),
) -> FixturePage:
    org = _get_org(db, slug)
    if status == "draft":
        return FixturePage(items=[], total=0, limit=limit, offset=offset)
    stmt = _apply_fixture_filters(
        select(Fixture).where(Fixture.organization_id == org.id),
        team_id=team_id,
        team=team,
        format_code=format_code,
        date_from=date_from,
        date_to=date_to,
        status=status,
        when=when,
        public_only=True,
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order = Fixture.starts_at.desc() if when == "completed" else Fixture.starts_at.asc()
    rows = db.scalars(stmt.order_by(order).limit(limit).offset(offset)).all()
    return FixturePage(
        items=[_fixture_public(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/v1/orgs/{slug}/fixtures/{fixture_id}", response_model=FixturePublic)
def get_public_fixture(
    slug: str, fixture_id: uuid.UUID, db: Session = Depends(get_db)
) -> FixturePublic:
    org = _get_org(db, slug)
    fixture = _fixture_for_org(db, org, fixture_id)
    if fixture.status not in PUBLIC_FIXTURE_STATUSES:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return _fixture_public(fixture)


@router.get("/v1/orgs/{slug}/admin/schedules", response_model=ScheduleAdminPage)
def list_admin_schedules(
    slug: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleAdminPage:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    stmt = select(Schedule).where(Schedule.organization_id == org.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Schedule.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return ScheduleAdminPage(
        items=[_schedule_admin(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/v1/orgs/{slug}/admin/schedules",
    response_model=ScheduleAdminOut,
    status_code=201,
)
def create_schedule(
    slug: str,
    body: ScheduleIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    code, name, overs = resolve_format(body.format_code, body.format_name, body.overs)
    row = Schedule(
        organization_id=org.id,
        name=body.name.strip(),
        season=body.season.strip(),
        competition=body.competition.strip(),
        format_code=code,
        format_name=name,
        overs=overs,
        timezone=_require_timezone(body.timezone),
        status=body.status,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="schedule.created",
        entity_type="schedule",
        entity_id=str(row.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"name": row.name, "status": row.status},
    )
    db.commit()
    db.refresh(row)
    return _schedule_admin(row)


@router.patch(
    "/v1/orgs/{slug}/admin/schedules/{schedule_id}",
    response_model=ScheduleAdminOut,
)
def update_schedule(
    slug: str,
    schedule_id: uuid.UUID,
    body: ScheduleUpdateIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    row = _schedule_for_org(db, org, schedule_id)
    data = body.model_dump(exclude_unset=True)
    if "timezone" in data and data["timezone"] is not None:
        data["timezone"] = _require_timezone(data["timezone"])
    if any(key in data for key in ("format_code", "format_name", "overs")):
        code, name, overs = resolve_format(
            data.get("format_code", row.format_code),
            data.get("format_name", row.format_name),
            data.get("overs", row.overs),
        )
        data["format_code"] = code
        data["format_name"] = name
        data["overs"] = overs
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(row, key, value)
    row.updated_at = utcnow()
    write_audit(
        db,
        action="schedule.updated",
        entity_type="schedule",
        entity_id=str(row.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={key: data[key] for key in data},
    )
    db.commit()
    db.refresh(row)
    return _schedule_admin(row)


@router.delete("/v1/orgs/{slug}/admin/schedules/{schedule_id}", status_code=204)
def delete_schedule(
    slug: str,
    schedule_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    row = _schedule_for_org(db, org, schedule_id)
    write_audit(
        db,
        action="schedule.deleted",
        entity_type="schedule",
        entity_id=str(row.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"name": row.name},
    )
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.get("/v1/orgs/{slug}/admin/fixtures", response_model=FixtureAdminPage)
def list_admin_fixtures(
    slug: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    team_id: uuid.UUID | None = None,
    team: str | None = None,
    format_code: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    when: str | None = None,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FixtureAdminPage:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    stmt = _apply_fixture_filters(
        select(Fixture).where(Fixture.organization_id == org.id),
        team_id=team_id,
        team=team,
        format_code=format_code,
        date_from=date_from,
        date_to=date_to,
        status=status,
        when=when,
        public_only=False,
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order = Fixture.starts_at.desc() if when == "completed" else Fixture.starts_at.asc()
    rows = db.scalars(stmt.order_by(order).limit(limit).offset(offset)).all()
    return FixtureAdminPage(
        items=[_fixture_admin(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/v1/orgs/{slug}/admin/fixtures",
    response_model=FixtureAdminOut,
    status_code=201,
)
def create_fixture(
    slug: str,
    body: FixtureIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FixtureAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    if body.schedule_id is not None:
        _schedule_for_org(db, org, body.schedule_id)
    home_id, home_name = _team_side(
        db, org, body.home_team_id, body.home_team_name, label="Home"
    )
    away_id, away_name = _team_side(
        db, org, body.away_team_id, body.away_team_name, label="Away"
    )
    if home_id is not None and home_id == away_id:
        raise HTTPException(status_code=422, detail="Home and away teams must differ")
    code, format_name, overs = resolve_format(body.format_code, body.format_name, body.overs)
    row = Fixture(
        organization_id=org.id,
        schedule_id=body.schedule_id,
        season=body.season.strip(),
        competition=body.competition.strip(),
        home_team_id=home_id,
        away_team_id=away_id,
        home_team_name=home_name,
        away_team_name=away_name,
        venue=body.venue.strip(),
        starts_at=_require_aware(body.starts_at),
        timezone=_require_timezone(body.timezone),
        format_code=code,
        format_name=format_name,
        overs=overs,
        status=body.status,
        result_summary=_clean_result(body.result_summary),
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="fixture.created",
        entity_type="fixture",
        entity_id=str(row.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"status": row.status, "format_code": row.format_code},
    )
    db.commit()
    db.refresh(row)
    return _fixture_admin(row)


@router.patch("/v1/orgs/{slug}/admin/fixtures/{fixture_id}", response_model=FixtureAdminOut)
def update_fixture(
    slug: str,
    fixture_id: uuid.UUID,
    body: FixtureUpdateIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FixtureAdminOut:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    row = _fixture_for_org(db, org, fixture_id)
    data = body.model_dump(exclude_unset=True)
    if "schedule_id" in data and data["schedule_id"] is not None:
        _schedule_for_org(db, org, data["schedule_id"])
    if "home_team_id" in data or "home_team_name" in data:
        home_id, home_name = _team_side(
            db,
            org,
            data.get("home_team_id", row.home_team_id),
            data.get("home_team_name", row.home_team_name),
            label="Home",
        )
        data["home_team_id"] = home_id
        data["home_team_name"] = home_name
    if "away_team_id" in data or "away_team_name" in data:
        away_id, away_name = _team_side(
            db,
            org,
            data.get("away_team_id", row.away_team_id),
            data.get("away_team_name", row.away_team_name),
            label="Away",
        )
        data["away_team_id"] = away_id
        data["away_team_name"] = away_name
    next_home = data.get("home_team_id", row.home_team_id)
    next_away = data.get("away_team_id", row.away_team_id)
    if next_home is not None and next_home == next_away:
        raise HTTPException(status_code=422, detail="Home and away teams must differ")
    if "starts_at" in data and data["starts_at"] is not None:
        data["starts_at"] = _require_aware(data["starts_at"])
    if "timezone" in data and data["timezone"] is not None:
        data["timezone"] = _require_timezone(data["timezone"])
    if any(key in data for key in ("format_code", "format_name", "overs")):
        code, format_name, overs = resolve_format(
            data.get("format_code", row.format_code),
            data.get("format_name", row.format_name),
            data.get("overs", row.overs),
        )
        data["format_code"] = code
        data["format_name"] = format_name
        data["overs"] = overs
    if "result_summary" in data:
        data["result_summary"] = _clean_result(data["result_summary"])
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(row, key, value)
    row.updated_at = utcnow()
    write_audit(
        db,
        action="fixture.updated",
        entity_type="fixture",
        entity_id=str(row.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"fields": sorted(data.keys()), "status": row.status},
    )
    db.commit()
    db.refresh(row)
    return _fixture_admin(row)


@router.delete("/v1/orgs/{slug}/admin/fixtures/{fixture_id}", status_code=204)
def delete_fixture(
    slug: str,
    fixture_id: uuid.UUID,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    org = _get_org(db, slug)
    require_org_admin(db, user, org.id)
    row = _fixture_for_org(db, org, fixture_id)
    write_audit(
        db,
        action="fixture.deleted",
        entity_type="fixture",
        entity_id=str(row.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"status": row.status},
    )
    db.delete(row)
    db.commit()
    return Response(status_code=204)
