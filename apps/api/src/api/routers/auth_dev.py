from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import create_dev_access_token, ensure_profile
from api.config import get_settings
from api.db import get_db
from api.models import Profile
from api.schemas import DevTokenRequest, DevTokenResponse, ProfileOut

router = APIRouter(tags=["auth-dev"])


@router.post("/v1/auth/dev-token", response_model=DevTokenResponse)
def issue_dev_token(
    body: DevTokenRequest,
    db: Session = Depends(get_db),
) -> DevTokenResponse:
    settings = get_settings()
    if settings.effective_auth_mode != "dev":
        raise HTTPException(
            status_code=404,
            detail="Dev token endpoint disabled when MC360_AUTH_MODE=supabase",
        )
    if body.user_id is not None:
        user_id = body.user_id
    else:
        existing = db.scalar(select(Profile).where(Profile.email == body.email))
        user_id = existing.id if existing is not None else uuid.uuid4()
    profile = ensure_profile(db, user_id, body.email)
    if body.display_name:
        profile.display_name = body.display_name
    db.commit()
    token = create_dev_access_token(user_id=user_id, email=body.email, settings=settings)
    return DevTokenResponse(
        access_token=token,
        user=ProfileOut(
            id=profile.id,
            email=profile.email,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            phone=profile.phone,
        ),
        note=(
            "Local/dev HS256 token only. Configure SUPABASE_URL + JWKS for production "
            "and set MC360_AUTH_MODE=supabase."
        ),
    )
