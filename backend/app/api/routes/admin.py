from typing import Annotated, Any
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.security import ROLE_ADMIN, CurrentUser, require_roles
from app.repositories import store
# Import the admin client you created in the separate file
from app.core.admin_priv import require_supabase_admin
from auth.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

_ROLE_PREFIXES: dict[str, str] = {
    "admin": "ADM",
    "doctor": "DOC",
    "nurse": "NUR",
    "record_officer": "REC",
    "pharmacist": "PHA",
    "lab_scientist": "LAB",
    "billing_officer": "BIL",
}


def _normalize_role_input(role: str) -> str:
    normalized = role.strip().lower().replace("-", " ")
    normalized = "_".join(normalized.split())
    if normalized not in _ROLE_PREFIXES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported role '{role}'.",
        )
    return normalized


def _split_display_name(display_name: str) -> tuple[str, str]:
    parts = [p for p in display_name.strip().split() if p]
    if not parts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="display_name is required.",
        )
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else parts[0]
    return first_name, last_name


def _generate_staff_id(role: str) -> str:
    return f"{_ROLE_PREFIXES[role]}-{secrets.randbelow(10_000):04d}"


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
    role = _normalize_role_input(body.role)
    first_name, last_name = _split_display_name(body.display_name)
    password_hash = hash_password(body.password)
    created_auth_user_id: str | None = None

    try:
        supabase_admin = require_supabase_admin()
        # STEP 1: Create user in Supabase Auth (Hidden 'auth' schema)
        # We use email_confirm=True so the admin-created user can log in immediately
        auth_res = supabase_admin.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "email_confirm": True,
            "user_metadata": {
                "display_name": body.display_name,
                "role": role,
            },
            "app_metadata": {
                "role": role,
            },
        })

        created_auth_user_id = getattr(getattr(auth_res, "user", None), "id", None)
        if not created_auth_user_id:
            raise RuntimeError("Auth user was created but user id was not returned.")

        # STEP 2: Use the ID from Auth to create the record in your 'public.users' table
        # This replaces your old 'store.add_user_invite' logic while matching
        # the required columns in public.users.
        last_insert_error: Exception | None = None
        inserted = False
        for _ in range(5):
            staff_id = _generate_staff_id(role)
            try:
                supabase_admin.table("users").insert({
                    "id": created_auth_user_id,
                    "staff_id": staff_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": body.email,
                    "password_hash": password_hash,
                    "role": role,
                    "status": "Offline",
                }).execute()
                inserted = True
                break
            except Exception as insert_error:
                # Retry on potential staff_id collision, fail fast otherwise.
                if "users_staff_id_key" in str(insert_error):
                    last_insert_error = insert_error
                    continue
                raise

        if not inserted:
            raise RuntimeError(f"Unable to generate unique staff_id: {last_insert_error}")

    except Exception as e:
        if created_auth_user_id:
            try:
                supabase_admin.auth.admin.delete_user(created_auth_user_id)
            except Exception:
                pass
        # Map any Supabase errors to a 400 Bad Request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Failed to invite user: {str(e)}"
        )
        
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
