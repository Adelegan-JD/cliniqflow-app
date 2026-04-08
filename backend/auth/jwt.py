from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import timedelta


JWT_ALGORITHM = "HS256"
JWT_ISSUER = os.getenv("JWT_ISSUER", "cliniqflow-backend")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "cliniqflow-client")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
)


class JWTError(ValueError):
    pass


class JWTExpiredError(JWTError):
    pass


class JWTValidationError(JWTError):
    pass


def _jwt_secret() -> bytes:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise JWTValidationError("JWT_SECRET is not set.")
    return secret.encode("utf-8")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _json_encode(data: dict) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _json_decode(data: bytes) -> dict:
    try:
        decoded = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JWTValidationError("JWT payload is not valid JSON.") from exc

    if not isinstance(decoded, dict):
        raise JWTValidationError("JWT payload must be a JSON object.")
    return decoded


def _sign(signing_input: bytes) -> str:
    signature = hmac.new(
        _jwt_secret(),
        signing_input,
        hashlib.sha256,
    ).digest()
    return _b64url_encode(signature)


def _now_timestamp() -> int:
    return int(time.time())


def _normalize_expiry(
    *,
    expires_in: timedelta | None = None,
    expires_in_seconds: int | None = None,
) -> int:
    if expires_in is not None and expires_in_seconds is not None:
        raise ValueError("Provide either expires_in or expires_in_seconds, not both.")

    if expires_in_seconds is not None:
        ttl_seconds = expires_in_seconds
    elif expires_in is not None:
        ttl_seconds = int(expires_in.total_seconds())
    else:
        raise ValueError("Token expiry is required.")

    if ttl_seconds <= 0:
        raise ValueError("Token expiry must be greater than zero.")

    return ttl_seconds


def create_jwt(
    *,
    subject: str,
    token_type: str,
    expires_in: timedelta | None = None,
    expires_in_seconds: int | None = None,
    additional_claims: dict | None = None,
) -> str:
    ttl_seconds = _normalize_expiry(
        expires_in=expires_in,
        expires_in_seconds=expires_in_seconds,
    )
    now = _now_timestamp()

    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": subject,
        "token_type": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + ttl_seconds,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": secrets.token_urlsafe(16),
    }
    if additional_claims:
        payload.update(additional_claims)

    encoded_header = _b64url_encode(_json_encode(header))
    encoded_payload = _b64url_encode(_json_encode(payload))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = _sign(signing_input)
    return f"{encoded_header}.{encoded_payload}.{signature}"


def decode_jwt(
    token: str,
    *,
    expected_token_type: str | None = None,
    verify_exp: bool = True,
) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise JWTValidationError("JWT must have exactly three parts.")

    encoded_header, encoded_payload, signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(signature, expected_signature):
        raise JWTValidationError("JWT signature is invalid.")

    header = _json_decode(_b64url_decode(encoded_header))
    payload = _json_decode(_b64url_decode(encoded_payload))

    if header.get("alg") != JWT_ALGORITHM:
        raise JWTValidationError("JWT algorithm is invalid.")
    if header.get("typ") != "JWT":
        raise JWTValidationError("JWT type is invalid.")

    now = _now_timestamp()
    if payload.get("iss") != JWT_ISSUER:
        raise JWTValidationError("JWT issuer is invalid.")
    if payload.get("aud") != JWT_AUDIENCE:
        raise JWTValidationError("JWT audience is invalid.")

    nbf = payload.get("nbf")
    if nbf is not None and now < int(nbf):
        raise JWTValidationError("JWT is not active yet.")

    if verify_exp:
        exp = payload.get("exp")
        if exp is None:
            raise JWTValidationError("JWT expiry is missing.")
        if now >= int(exp):
            raise JWTExpiredError("JWT has expired.")

    if expected_token_type and payload.get("token_type") != expected_token_type:
        raise JWTValidationError("JWT token_type is invalid.")

    if not payload.get("sub"):
        raise JWTValidationError("JWT subject is missing.")

    return payload


def create_access_token(user: dict) -> str:
    return create_jwt(
        subject=user["staff_id"],
        token_type="access",
        expires_in_seconds=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        additional_claims={
            "email": user["email"],
            "role": user["role"],
        },
    )


def create_refresh_token(user: dict) -> str:
    return create_jwt(
        subject=user["staff_id"],
        token_type="refresh",
        expires_in_seconds=JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        additional_claims={
            "email": user["email"],
            "role": user["role"],
        },
    )


def token_expiry_seconds(token_type: str) -> int:
    if token_type == "access":
        return JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    if token_type == "refresh":
        return JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    raise ValueError(f"Unsupported token_type '{token_type}'.")
