from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from database.config import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "backend",
        "persistence": "postgres" if engine is not None else "memory",
    }


@router.get("/health/ready")
def readiness() -> dict:
    """Used by the deployment platform; never claim readiness without PostgreSQL."""
    if engine is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not configured")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable") from None
    return {"status": "ready", "service": "backend"}


@router.get("/")
def root() -> dict:
    return {"service": "cliniqflow-backend", "docs": "/docs", "health": "/health"}
