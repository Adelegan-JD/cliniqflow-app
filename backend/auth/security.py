from __future__ import annotations

import os
from collections.abc import Iterable

import bcrypt
from sqlalchemy import text

from database.config import engine


DEFAULT_BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
MAX_BCRYPT_PASSWORD_BYTES = 72


def _normalize_role(role: str) -> str:
    return role.strip().lower()


def _validate_password_input(password: str) -> None:
    if not isinstance(password, str) or not password:
        raise ValueError("Password is required.")

    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError(
            f"Password must not exceed {MAX_BCRYPT_PASSWORD_BYTES} bytes for bcrypt."
        )


def hash_password(password: str, rounds: int | None = None) -> str:
    _validate_password_input(password)

    work_factor = rounds or DEFAULT_BCRYPT_ROUNDS
    if work_factor < 4 or work_factor > 31:
        raise ValueError("BCRYPT rounds must be between 4 and 31.")

    password_bytes = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=work_factor),
    )
    return hashed_password.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def resolve_password_hash(*, password: str | None = None, password_hash: str | None = None) -> str:
    if password and password_hash:
        raise ValueError("Provide either 'password' or 'password_hash', not both.")

    if password_hash:
        return password_hash

    if password:
        return hash_password(password)

    raise ValueError("Either 'password' or 'password_hash' is required.")


def _fetch_staff_auth_row(conn, email: str) -> dict | None:
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
                password_hash,
                role,
                department,
                license_number,
                status,
                created_at,
                updated_at
            FROM users
            WHERE email = :email;
            """
        ),
        {"email": email},
    )

    row = result.mappings().first()
    return dict(row) if row else None


def authenticate_staff(email: str, password: str, conn=None) -> dict | None:
    if not email or not password:
        return None

    if conn is not None:
        staff = _fetch_staff_auth_row(conn, email)
    else:
        with engine.connect() as connection:
            staff = _fetch_staff_auth_row(connection, email)

    if not staff:
        return None

    if not verify_password(password, staff["password_hash"]):
        return None

    staff.pop("password_hash", None)
    return staff


def is_authorized(user: dict | None, allowed_roles: Iterable[str]) -> bool:
    if not user or "role" not in user:
        return False

    normalized_allowed_roles = {_normalize_role(role) for role in allowed_roles}
    return _normalize_role(user["role"]) in normalized_allowed_roles


def require_roles(user: dict | None, allowed_roles: Iterable[str]) -> None:
    if is_authorized(user, allowed_roles):
        return

    allowed = ", ".join(sorted({_normalize_role(role) for role in allowed_roles}))
    raise PermissionError(f"User is not authorized. Allowed roles: {allowed}.")
