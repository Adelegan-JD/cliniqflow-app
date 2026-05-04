from fastapi import APIRouter

from database.config import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "backend",
        "persistence": "postgres" if engine is not None else "memory",
    }


@router.get("/")
def root() -> dict:
    return {"service": "cliniqflow-backend", "docs": "/docs", "health": "/health"}
