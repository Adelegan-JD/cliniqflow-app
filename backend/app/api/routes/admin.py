from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from app.core.security import ROLE_ADMIN, CurrentUser, require_roles
from app.repositories.memory_store import store

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
    """Return staff users (stub until Supabase Auth admin)."""
    return [u.copy() for u in store.users]


@router.post("/invite-user")
def invite_user(
    body: InviteUserRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, str]:
    """Stub: records intent; production should call Supabase Admin API."""
    store.add_user_invite(
        email=body.email,
        display_name=body.display_name,
        role=body.role,
    )
    return {
        "message": f"Invitation recorded for {body.email}. Complete provisioning in Supabase Auth.",
    }


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
