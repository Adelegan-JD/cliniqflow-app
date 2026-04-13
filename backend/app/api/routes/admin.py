from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.security import ROLE_ADMIN, CurrentUser, require_roles
from app.repositories import store

router = APIRouter(prefix="/admin", tags=["admin"])


class InviteUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str
    display_name: str


@router.get("/users", response_model=list[dict[str, Any]])
def list_users(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> list[dict[str, Any]]:
    rows = store.list_users_admin()
    return [
        {"id": r.get("id"), "name": r.get("name", ""), "email": r.get("email", ""), "role": r.get("role", "")}
        for r in rows
    ]


@router.post("/invite-user")
def invite_user(
    body: InviteUserRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, str]:
    try:
        store.add_user_invite(
            email=body.email,
            display_name=body.display_name,
            role=body.role,
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"message": f"Staff account created for {body.email}."}


@router.get("/stats")
def admin_stats(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, int]:
    s = store.admin_stats()
    return {
        "totalPatients": s["totalPatients"],
        "visitsToday": s["visitsToday"],
        "newRegistrationsThisMonth": s["newRegistrationsThisMonth"],
        "doctorQueue": s["doctorQueue"],
    }


@router.get("/metrics")
def admin_metrics(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, Any]:
    """Same counters as /admin/stats; extended shape for dashboards that expect `metrics`."""
    s = store.admin_stats()
    return {
        "totalPatients": s["totalPatients"],
        "visitsToday": s["visitsToday"],
        "newRegistrationsThisMonth": s["newRegistrationsThisMonth"],
        "doctorQueue": s["doctorQueue"],
    }


@router.get("/sync/status")
def sync_status(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, Any]:
    """Placeholder until an external sync job exists."""
    return {"enabled": False, "lastRun": None, "message": "No sync integration configured."}


@router.post("/sync/run")
def sync_run(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, Any]:
    return {"ok": False, "message": "No sync integration configured."}


@router.get("/logs")
def admin_logs(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> list[dict[str, Any]]:
    """Placeholder; wire to logging/audit store when available."""
    return []
