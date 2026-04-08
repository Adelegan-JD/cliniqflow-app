from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import text

from auth.jwt import (
    JWTValidationError,
    create_access_token,
    create_refresh_token,
    decode_jwt,
    token_expiry_seconds,
)
from auth.security import authenticate_staff, require_roles
from database.config import engine


def _sanitize_staff(row: dict) -> dict:
    sanitized = dict(row)
    sanitized.pop("password_hash", None)
    return sanitized


def _fetch_staff_by_staff_id(conn, staff_id: str) -> dict | None:
    result = conn.execute(
        text(
            """
            SELECT
                id,
                staff_id,
                first_name,
                last_name,
                other_names,
                email,
                phone,
                role,
                department,
                license_number,
                status,
                created_at,
                updated_at
            FROM users
            WHERE staff_id = :staff_id;
            """
        ),
        {"staff_id": staff_id},
    )

    row = result.mappings().first()
    return dict(row) if row else None


def issue_token_pair(user: dict) -> dict:
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "access_expires_in": token_expiry_seconds("access"),
        "refresh_expires_in": token_expiry_seconds("refresh"),
    }


def login_staff(email: str, password: str, conn=None) -> dict | None:
    if conn is not None:
        user = authenticate_staff(email, password, conn=conn)
    else:
        user = authenticate_staff(email, password)

    if not user:
        return None

    return {
        "user": user,
        "tokens": issue_token_pair(user),
    }


def get_current_staff(token: str, *, conn=None) -> dict | None:
    payload = decode_jwt(token, expected_token_type="access")

    if conn is not None:
        return _fetch_staff_by_staff_id(conn, payload["sub"])

    with engine.connect() as connection:
        return _fetch_staff_by_staff_id(connection, payload["sub"])


def refresh_staff_session(refresh_token: str, *, conn=None) -> dict:
    payload = decode_jwt(refresh_token, expected_token_type="refresh")

    if conn is not None:
        user = _fetch_staff_by_staff_id(conn, payload["sub"])
    else:
        with engine.connect() as connection:
            user = _fetch_staff_by_staff_id(connection, payload["sub"])

    if not user:
        raise JWTValidationError("Refresh token subject does not map to an active staff user.")

    return {
        "user": user,
        "tokens": issue_token_pair(user),
    }


def authorize_staff_token(
    token: str,
    allowed_roles: Iterable[str],
    *,
    conn=None,
) -> dict:
    user = get_current_staff(token, conn=conn)
    require_roles(user, allowed_roles)
    return user


def extract_bearer_token(authorization_header: str | None) -> str:
    if not authorization_header:
        raise JWTValidationError("Authorization header is missing.")

    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise JWTValidationError("Authorization header must use the Bearer scheme.")
    return token.strip()
