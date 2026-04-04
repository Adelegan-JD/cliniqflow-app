from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import (
    ROLE_ADMIN,
    ROLE_DOCTOR,
    ROLE_NURSE,
    ROLE_RECORD_OFFICER,
    CurrentUser,
    require_roles,
)
from app.repositories.memory_store import store

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[dict[str, Any]])
def list_patients_resource(
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, ROLE_RECORD_OFFICER)),
    ],
) -> list[dict[str, Any]]:
    """REST list for integrations; prefer role-scoped routes for UX."""
    return list(store.patients.values())


@router.get("/{patient_id}", response_model=dict[str, Any])
def get_patient(
    patient_id: str,
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, ROLE_RECORD_OFFICER)),
    ],
) -> dict[str, Any]:
    p = store.get_patient(patient_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return p
