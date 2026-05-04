import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("CLINIQ_DEV_BYPASS_AUTH", "true")

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers_admin() -> dict[str, str]:
    return {
        "Authorization": "Bearer dev-test-token",
        "X-Debug-Role": "admin",
        "X-Debug-User-Id": "test-admin",
    }


@pytest.fixture
def auth_headers_doctor() -> dict[str, str]:
    return {
        "Authorization": "Bearer dev-test-token",
        "X-Debug-Role": "doctor",
        "X-Debug-User-Id": "test-doc",
    }


@pytest.fixture
def auth_headers_nurse() -> dict[str, str]:
    return {
        "Authorization": "Bearer dev-test-token",
        "X-Debug-Role": "nurse",
        "X-Debug-User-Id": "test-nurse",
    }


@pytest.fixture
def auth_headers_record_officer() -> dict[str, str]:
    return {
        "Authorization": "Bearer dev-test-token",
        "X-Debug-Role": "record_officer",
        "X-Debug-User-Id": "test-ro",
    }
