from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthUser, get_current_user, get_membership, require_org_admin
from api.db import get_db
from api.models import Membership, Organization, Profile, utcnow
from api.schemas import (
    MembershipDecisionIn,
    MembershipOut,
    MembershipRequestIn,
    MeResponse,
    ProfileOut,
    ProfileUpdateIn,
)
from api.services import membership_to_out, write_audit

router = APIRouter(tags=["me", "memberships"])


def _profile_out(profile: Profile) -> ProfileOut:
    return ProfileOut(
        id=profile.id,
        email=profile.email,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        phone=profile.phone,
    )


def _load_memberships(db: Session, user_id: uuid.UUID) -> list[MembershipOut]:
    rows = db.execute(
        select(Membership, Organization)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(Membership.user_id == user_id)
        .order_by(Organization.slug.asc())
    ).all()
    return [membership_to_out(m, org) for m, org in rows]


@router.get("/v1/me", response_model=MeResponse)
def get_me(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeResponse:
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    memberships = _load_memberships(db, user.id)
    approved = [m for m in memberships if m.status == "approved"]
    return MeResponse(user=_profile_out(profile), memberships=memberships, approved_clubs=approved)


@router.patch("/v1/me", response_model=ProfileOut)
def update_me(
    body: ProfileUpdateIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    if body.display_name is None and body.phone is None:
        raise HTTPException(status_code=400, detail="No profile fields to update")
    if body.display_name is not None:
        profile.display_name = body.display_name.strip()
    if body.phone is not None:
        profile.phone = body.phone.strip() or None
    profile.updated_at = utcnow()
    write_audit(
        db,
        action="profile.updated",
        entity_type="profile",
        entity_id=str(profile.id),
        actor_user_id=user.id,
    )
    db.commit()
    db.refresh(profile)
    return _profile_out(profile)


@router.get("/v1/me/memberships", response_model=list[MembershipOut])
def list_my_memberships(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipOut]:
    return _load_memberships(db, user.id)


@router.get("/v1/me/clubs", response_model=list[MembershipOut])
def list_approved_clubs(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipOut]:
    return [m for m in _load_memberships(db, user.id) if m.status == "approved"]


@router.post("/v1/me/memberships", response_model=MembershipOut, status_code=201)
def request_membership(
    body: MembershipRequestIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MembershipOut:
    org = db.scalar(select(Organization).where(Organization.slug == body.organization_slug))
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing = get_membership(db, user.id, org.id)
    if existing is not None:
        if existing.status == "approved":
            raise HTTPException(status_code=409, detail="Already a member")
        if existing.status == "pending":
            return membership_to_out(existing, org)
        # rejected, suspended, or revoked → re-request as a pending member
        existing.status = "pending"
        existing.role = "member"
        existing.requested_at = utcnow()
        existing.decided_at = None
        existing.decided_by = None
        write_audit(
            db,
            action="membership.rerequested",
            entity_type="membership",
            entity_id=str(existing.id),
            organization_id=org.id,
            actor_user_id=user.id,
        )
        db.commit()
        db.refresh(existing)
        return membership_to_out(existing, org)

    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role="member",
        status="pending",
        requested_at=utcnow(),
    )
    db.add(membership)
    db.flush()
    write_audit(
        db,
        action="membership.requested",
        entity_type="membership",
        entity_id=str(membership.id),
        organization_id=org.id,
        actor_user_id=user.id,
    )
    db.commit()
    db.refresh(membership)
    return membership_to_out(membership, org)


@router.get("/v1/orgs/{slug}/memberships", response_model=list[MembershipOut])
def list_org_memberships(
    slug: str,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipOut]:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    require_org_admin(db, user, org.id)
    rows = db.execute(
        select(Membership, Organization)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(Membership.organization_id == org.id)
        .order_by(Membership.requested_at.asc())
    ).all()
    return [membership_to_out(m, o) for m, o in rows]


@router.post("/v1/orgs/{slug}/memberships/{membership_id}/decision", response_model=MembershipOut)
def decide_membership(
    slug: str,
    membership_id: uuid.UUID,
    body: MembershipDecisionIn,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MembershipOut:
    org = db.scalar(select(Organization).where(Organization.slug == slug))
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    require_org_admin(db, user, org.id)

    membership = db.get(Membership, membership_id)
    if membership is None or membership.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Membership not found")

    # Prevent self-approval / self-privilege changes, including suspend and role grants.
    if membership.user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve or reject your own membership",
        )
    if body.role is not None and body.decision != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role can only be set when approving a membership",
        )

    membership.status = body.decision
    if body.decision == "approved":
        if body.role is not None:
            membership.role = body.role
        elif membership.role not in {"member", "admin"}:
            membership.role = "member"
    else:
        # Rejection and suspension drop elevated roles so status checks cannot be skipped.
        membership.role = "member"
    membership.decided_at = utcnow()
    membership.decided_by = user.id

    write_audit(
        db,
        action=f"membership.{body.decision}",
        entity_type="membership",
        entity_id=str(membership.id),
        organization_id=org.id,
        actor_user_id=user.id,
        meta={"role": membership.role, "subject_user_id": str(membership.user_id)},
    )
    db.commit()
    db.refresh(membership)
    return membership_to_out(membership, org)
