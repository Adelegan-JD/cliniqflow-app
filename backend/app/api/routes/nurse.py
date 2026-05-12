from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import ROLE_NURSE, CurrentUser, require_roles
from app.repositories import store

router = APIRouter(prefix="/nurse", tags=["nurse"])


def _normalize_nurse_queue_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "visit_id": item.get("visit_id"),
        "patient_id": item.get("patient_id"),
        "patientId": item.get("patient_id"),
        "name": item.get("patient_name") or item.get("name") or "",
        "age": item.get("age"),
        "sex": item.get("gender") or item.get("sex"),
        "gender": item.get("gender"),
        "status": item.get("status") or "awaiting_triage",
        "urgency": item.get("urgency") or "normal",
        "visit_status": item.get("visit_status"),
        "triage_status": item.get("triage_status"),
        "created_at": item.get("created_at"),
    }


@router.get("/queue", response_model=list[dict[str, Any]])
@router.get("/triage-queue", response_model=list[dict[str, Any]])
def nurse_queue(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> list[dict[str, Any]]:
    """Visits waiting for triage (same underlying rows as record-officer pre-clinical queue)."""
    return [_normalize_nurse_queue_item(item) for item in store.list_visits_for_nurse_queue()]


@router.get("/stats", response_model=dict[str, int])
def nurse_stats(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> dict[str, int]:
    """Nurse dashboard statistics aligned with frontend nurse dashboard metrics."""
    return store.doctor_dashboard_stats()


class TriageSubmitRequest(BaseModel):
    visit_id: str | None = None
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
        visit_id = body.visit_id
        # If frontend did not provide a visit id (new registration), create a visit
        if not visit_id:
            # create_visit expects patient_id and returns a visit row
            created = store.create_visit(
                patient_id=body.patient_id,
                reason_for_visit=None,
                department=None,
                checked_in_by=staff_id,
            )
            if not created:
                raise ValueError("Failed to create visit for patient")
            visit_id = created.get("visit_id") or created.get("visit_uuid") or created.get("visit_id")

        # ensure visit_id is a string for downstream save_triage
        visit_id = str(visit_id)
        ev = store.save_triage(
            visit_id=visit_id,
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
