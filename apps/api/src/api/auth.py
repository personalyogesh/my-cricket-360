"""Supabase JWT validation and club-scoped authorization helpers."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from api.db import get_db
from api.models import Membership, Profile, utcnow

bearer_scheme = HTTPBearer(auto_error=False)

# Simple in-process JWKS client cache
_jwks_clients: dict[str, PyJWKClient] = {}


@dataclass(frozen=True, slots=True)
class AuthUser:
    id: uuid.UUID
    email: str | None
    claims: dict[str, Any]


def _get_jwks_client(settings: Settings) -> PyJWKClient:
    url = settings.jwks_url
    if not url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase JWKS URL is not configured",
        )
    if url not in _jwks_clients:
        _jwks_clients[url] = PyJWKClient(url, cache_keys=True, lifespan=3600)
    return _jwks_clients[url]


def create_dev_access_token(
    *,
    user_id: uuid.UUID | str,
    email: str | None = None,
    settings: Settings | None = None,
    expires_in: int = 3600,
) -> str:
    """HS256 token for local/tests when Supabase credentials are absent."""
    settings = settings or get_settings()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": settings.supabase_jwt_audience,
        "iss": settings.jwt_issuer,
        "role": "authenticated",
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, settings.dev_jwt_secret, algorithm="HS256")


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    mode = settings.effective_auth_mode

    if mode == "dev":
        try:
            return jwt.decode(
                token,
                settings.dev_jwt_secret,
                algorithms=["HS256"],
                audience=settings.supabase_jwt_audience,
                issuer=settings.jwt_issuer,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            ) from exc

    # supabase mode — verify via JWKS (RS256/ES256)
    try:
        client = _get_jwks_client(settings)
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=settings.supabase_jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Supabase token: {exc}",
        ) from exc


def ensure_profile(db: Session, user_id: uuid.UUID, email: str | None) -> Profile:
    profile = db.get(Profile, user_id)
    if profile is None:
        profile = Profile(
            id=user_id,
            email=email,
            display_name=(email.split("@")[0] if email else "Member"),
        )
        db.add(profile)
        db.flush()
    else:
        if email and profile.email != email:
            profile.email = email
            profile.updated_at = utcnow()
    return profile


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    claims = decode_access_token(credentials.credentials, settings)
    try:
        user_id = uuid.UUID(str(claims["sub"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject"
        ) from exc
    email = claims.get("email")
    ensure_profile(db, user_id, email)
    db.commit()
    return AuthUser(id=user_id, email=email, claims=claims)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthUser | None:
    if credentials is None:
        return None
    return get_current_user(credentials, db, settings)


def get_membership(
    db: Session, user_id: uuid.UUID, organization_id: uuid.UUID
) -> Membership | None:
    return db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
        )
    )


def require_org_member(
    db: Session,
    user: AuthUser,
    organization_id: uuid.UUID,
    *,
    roles: set[str] | None = None,
) -> Membership:
    membership = get_membership(db, user.id, organization_id)
    if membership is None or membership.status != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a club member")
    if roles is not None and membership.role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return membership


def require_org_admin(db: Session, user: AuthUser, organization_id: uuid.UUID) -> Membership:
    return require_org_member(db, user, organization_id, roles={"admin"})


def probe_supabase_jwks(settings: Settings | None = None) -> dict[str, Any]:
    """Diagnostic helper for setup instructions / health."""
    settings = settings or get_settings()
    if not settings.jwks_url:
        return {"configured": False, "reason": "SUPABASE_URL / JWKS not set"}
    try:
        response = httpx.get(settings.jwks_url, timeout=5.0)
        return {
            "configured": True,
            "url": settings.jwks_url,
            "status_code": response.status_code,
            "ok": response.is_success,
        }
    except Exception as exc:  # noqa: BLE001
        return {"configured": True, "url": settings.jwks_url, "ok": False, "error": str(exc)}
