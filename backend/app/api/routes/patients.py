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
from app.repositories import store
from app.schemas.workflows import RegisterPatientBody

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=dict[str, Any])
def create_patient(
    body: RegisterPatientBody,
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_RECORD_OFFICER, ROLE_ADMIN)),
    ],
) -> dict[str, Any]:
    """Same behaviour as POST /record-officer/register-patient for REST-style clients."""
    data = body.model_dump()
    row = store.register_patient(data, registered_by=_user.staff_id)
    return {"pid": row["pid"], "id": row["id"], **row}


@router.get("", response_model=list[dict[str, Any]])
def list_patients_resource(
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, ROLE_RECORD_OFFICER)),
    ],
) -> list[dict[str, Any]]:
    """REST list for integrations; prefer role-scoped routes for UX."""
    return store.list_patients(None)


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
