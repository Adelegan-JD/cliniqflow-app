"""HTTP client for backend → ai_engine calls. Transport only; no models or inference here."""

from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


def _base() -> str:
    base = (settings.ai_engine_url or "").strip().rstrip("/")
    if not base:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI engine URL is not configured",
        )
    return base


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.ai_engine_token}"}


def post_json(path: str, payload: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
    url = f"{_base()}{path}"
    try:
        r = httpx.post(url, json=payload, headers=_headers(), timeout=timeout)
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable",
        ) from None
    if r.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service returned an error",
        )
    try:
        data = r.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Invalid response from AI service",
        ) from None
    if r.status_code >= 400:
        msg = "Request failed"
        if isinstance(data, dict):
            err = data.get("error") or {}
            if isinstance(err, dict) and err.get("message"):
                msg = err["message"]
            elif data.get("detail"):
                msg = str(data["detail"])
        raise HTTPException(status_code=r.status_code, detail=msg)
    return data


def post_multipart(
    path: str,
    files: dict[str, Any],
    data: dict[str, str],
    timeout: float = 120.0,
) -> dict[str, Any]:
    url = f"{_base()}{path}"
    h = {"Authorization": f"Bearer {settings.ai_engine_token}"}
    try:
        r = httpx.post(url, files=files, data=data, headers=h, timeout=timeout)
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI transcription service is unavailable",
        ) from None
    if r.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI transcription service returned an error",
        )
    try:
        data = r.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Invalid response from AI transcription service",
        ) from None
    if r.status_code >= 400:
        msg = "Transcription request failed"
        if isinstance(data, dict):
            err = data.get("error") or {}
            if isinstance(err, dict) and err.get("message"):
                msg = str(err["message"])
            elif data.get("detail"):
                msg = str(data["detail"])
        raise HTTPException(status_code=r.status_code, detail=msg)
    return data
