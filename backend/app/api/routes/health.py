from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "backend"}


@router.get("/")
def root() -> dict:
    return {"service": "cliniqflow-backend", "docs": "/docs", "health": "/health"}
