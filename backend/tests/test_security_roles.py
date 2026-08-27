import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import get_current_user


def test_editable_user_metadata_cannot_grant_admin_role(monkeypatch):
    """Only administrator-controlled app_metadata is a role source."""
    monkeypatch.setattr(settings, "cliniq_dev_bypass_auth", False)
    monkeypatch.setattr(settings, "supabase_url", "https://auth.example.test")
    secret = "test-secret-with-at-least-thirty-two-bytes"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_jwt_verify_aud", True)
    token = jwt.encode(
        {
            "sub": "staff-1", "email": "doctor@example.test",
            "iss": "https://auth.example.test/auth/v1", "aud": "authenticated",
            "user_metadata": {"role": "admin"},
            "app_metadata": {"role": "doctor"},
        },
        secret, algorithm="HS256",
    )
    user = get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    assert user.role == "doctor"


def test_production_settings_reject_localhost_and_missing_database(monkeypatch):
    monkeypatch.setattr(settings, "app_environment", "production")
    monkeypatch.setattr(settings, "database_url", "")
    monkeypatch.setattr(settings, "supabase_url", "https://auth.example.test")
    monkeypatch.setattr(settings, "supabase_jwt_secret", "x" * 32)
    monkeypatch.setattr(settings, "ai_engine_token", "x" * 32)
    monkeypatch.setattr(settings, "cors_origins", "http://localhost:5173")
    monkeypatch.setattr(settings, "cliniq_dev_bypass_auth", False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        settings.validate_production()
