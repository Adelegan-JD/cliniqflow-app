from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import ROLE_ADMIN, ROLE_DOCTOR, CurrentUser, require_roles
from app.repositories import store
from app.schemas.discharge import DischargeSummaryUpsert

router = APIRouter(prefix="/discharge-summaries", tags=["discharge summaries"])


@router.get("/admission/{admission_id}", response_model=dict[str, Any])
def get_discharge_summary(
    admission_id: str,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR))],
) -> dict[str, Any]:
    row = store.get_discharge_summary(admission_id)
    if not row:
        raise HTTPException(status_code=404, detail="Discharge summary not found")
    return row


@router.put("/admission/{admission_id}", response_model=dict[str, Any])
def save_discharge_summary(
    admission_id: str,
    body: DischargeSummaryUpsert,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR))],
) -> dict[str, Any]:
    row = store.upsert_discharge_summary(admission_id, body.model_dump(), user.staff_id)
    if not row:
        raise HTTPException(status_code=409, detail="Admission was not found or discharge summary is already final")
    return row
