from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text

from app.core.config import settings
from database.config import engine

security = HTTPBearer(auto_error=False)

ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_NURSE = "nurse"
ROLE_RECORD_OFFICER = "record_officer"


@dataclass
class CurrentUser:
    id: str
    email: str | None
    role: str
    staff_id: str | None = None


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
    opts: dict = {"verify_aud": settings.supabase_jwt_verify_aud}
    decode_kwargs: dict = {
        "options": opts,
        "issuer": settings.resolved_supabase_jwt_issuer,
    }
    if settings.supabase_jwt_verify_aud:
        decode_kwargs["audience"] = "authenticated"

    try:
        alg = str((jwt.get_unverified_header(token) or {}).get("alg") or "").upper()
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e

    try:
        if alg.startswith("HS"):
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                **decode_kwargs,
            )

        signing_key = _supabase_jwks_client().get_signing_key_from_jwt(token).key
        accepted_algs = [alg] if alg else ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]
        return jwt.decode(
            token,
            signing_key,
            algorithms=accepted_algs,
            **decode_kwargs,
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


@lru_cache(maxsize=1)
def _supabase_jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(settings.resolved_supabase_jwks_url)


def _resolve_staff_id_by_email(email: str | None) -> str | None:
    if not email or engine is None:
        return None

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT staff_id
                FROM users
                WHERE lower(email) = lower(:email)
                LIMIT 1;
                """
            ),
            {"email": email},
        ).mappings().first()

    return row["staff_id"] if row else None


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    x_debug_role: Annotated[str | None, Header()] = None,
    x_debug_user_id: Annotated[str | None, Header()] = None,
    x_debug_staff_id: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = creds.credentials

    if settings.cliniq_dev_bypass_auth:
        role = _normalize_role(x_debug_role or "admin")
        sid = x_debug_staff_id or "DEV-STAFF-0001"
        return CurrentUser(
            id=x_debug_user_id or "dev-user",
            email="dev@local",
            role=role,
            staff_id=sid,
        )

    if os.getenv("JWT_SECRET"):
        from auth.jwt import JWTValidationError
        from auth.service import get_current_staff

        try:
            staff = get_current_staff(token)
        except JWTValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
        return CurrentUser(
            id=str(staff["id"]), # type: ignore
            email=staff.get("email"), # pyright: ignore[reportOptionalMemberAccess]
            role=_normalize_role(staff.get("role")), # type: ignore
            staff_id=staff.get("staff_id"), # type: ignore
        )

    payload = _decode_supabase_jwt(token)
    sub = str(payload.get("sub") or "")
    email = payload.get("email")
    meta = payload.get("user_metadata") or {}
    app_meta = payload.get("app_metadata") or {}
    role_raw = meta.get("role") or app_meta.get("role")
    role = _normalize_role(str(role_raw) if role_raw else None)
    return CurrentUser(
        id=sub,
        email=email,
        role=role,
        staff_id=_resolve_staff_id_by_email(email),
    )


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
