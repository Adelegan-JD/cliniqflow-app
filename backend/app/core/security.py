from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

security = HTTPBearer(auto_error=False)

# Normalized role strings used for RBAC
ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_NURSE = "nurse"
ROLE_RECORD_OFFICER = "record_officer"


@dataclass
class CurrentUser:
    id: str
    email: str | None
    role: str


def _normalize_role(raw: str | None) -> str:
    if not raw:
        return ROLE_NURSE
    s = raw.strip().lower().replace("-", " ")
    s = "_".join(s.split())
    if "record" in s and "officer" in s:
        return ROLE_RECORD_OFFICER
    if s in (ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, ROLE_RECORD_OFFICER):
        return s
    return s


def _decode_supabase_jwt(token: str) -> dict:
    try:
        # Supabase uses HS256 and audience "authenticated" for end-user JWTs
        opts: dict = {"verify_aud": settings.supabase_jwt_verify_aud}
        extra: dict = {}
        if settings.supabase_jwt_verify_aud:
            extra["audience"] = "authenticated"
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            **extra,
            options=opts,
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_debug_role: Annotated[str | None, Header()] = None,
    x_debug_user_id: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = creds.credentials

    if settings.cliniq_dev_bypass_auth:
        role = _normalize_role(x_debug_role or "admin")
        return CurrentUser(
            id=x_debug_user_id or "dev-user",
            email="dev@local",
            role=role,
        )

    payload = _decode_supabase_jwt(token)
    sub = str(payload.get("sub") or "")
    email = payload.get("email")
    meta = payload.get("user_metadata") or {}
    app_meta = payload.get("app_metadata") or {}
    role_raw = meta.get("role") or app_meta.get("role")
    role = _normalize_role(str(role_raw) if role_raw else None)
    return CurrentUser(id=sub, email=email, role=role)


def require_roles(*allowed: str):
    allowed_set = set(allowed)

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return user

    return checker
