from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import ROLE_NURSE, CurrentUser, require_roles
from app.repositories import store

router = APIRouter(prefix="/nurse", tags=["nurse"])


@router.get("/queue", response_model=list[dict[str, Any]])
def nurse_queue(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> list[dict[str, Any]]:
    """Visits waiting for triage (same underlying rows as record-officer pre-clinical queue)."""
    return store.list_visits_for_nurse_queue()


class TriageSubmitRequest(BaseModel):
    visit_id: str
    patient_id: str
    vitals: dict[str, Any] = Field(default_factory=dict)
    urgency_level: str | None = Field(
        default=None,
        description="emergency | urgent | normal (optional if only storing vitals)",
    )


@router.get("/triage-records", response_model=list[dict[str, Any]])
def triage_records(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
    urgency: str | None = Query(None),
    search: str | None = Query(None),
) -> list[dict[str, Any]]:
    return store.list_triage_records(urgency, search)


def _submit_triage(
    body: TriageSubmitRequest, staff_id: str | None
) -> dict[str, Any]:
    try:
        ev = store.save_triage(
            visit_id=body.visit_id,
            patient_id=body.patient_id,
            vitals=body.vitals,
            urgency=body.urgency_level,
            nurse_staff_id=staff_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit or patient mismatch",
        )
    return ev


@router.post("/triage")
def submit_triage(
    body: TriageSubmitRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> dict[str, Any]:
    return _submit_triage(body, _user.staff_id)


@router.post("/complete-triage")
def complete_triage(
    body: TriageSubmitRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> dict[str, Any]:
    """Alias for POST /nurse/triage (product name)."""
    return _submit_triage(body, _user.staff_id)
