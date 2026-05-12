from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import ROLE_DOCTOR, CurrentUser, require_roles
from app.repositories import store

router = APIRouter(prefix="/doctor", tags=["doctor"])


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


class SoapSummaryIn(BaseModel):
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""


class SaveVisitRequest(BaseModel):
    visit_id: str
    patient_id: str | None = None
    transcript: str = ""
    soap_summary: SoapSummaryIn
    prescriptions: list[dict[str, Any]] = Field(default_factory=list)
    doctor_notes: str | None = None


@router.get("/stats")
def doctor_stats(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, int]:
    return store.doctor_dashboard_stats()


@router.get("/queue", response_model=list[dict[str, Any]])
def doctor_queue(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> list[dict[str, Any]]:
    return store.list_visits_for_doctor_queue()


@router.get("/nurse-queue-awareness", response_model=list[dict[str, Any]])
def nurse_queue_awareness_for_doctor(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> list[dict[str, Any]]:
    """Doctor read-only view of the same nurse triage queue (awareness only)."""
    return [_normalize_nurse_queue_item(item) for item in store.list_visits_for_nurse_queue()]


@router.get("/triaged-queue", response_model=list[dict[str, Any]])
def triaged_queue(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> list[dict[str, Any]]:
    """Get all patients who have completed triage and are awaiting doctor consultation."""
    return store.list_triaged_patients_for_doctor()


@router.post("/start-exam")
def start_exam(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
    visit_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    row = store.start_exam(visit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found or not waiting for doctor",
        )
    return row


@router.post("/cancel-exam")
def cancel_exam(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
    visit_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    row = store.cancel_exam(visit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found or no exam in progress",
        )
    return row


@router.post("/end-consultation")
def end_consultation(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
    visit_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    """End consultation and mark visit as completed."""
    row = store.end_consultation(visit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found or not in consultation",
        )
    return row


@router.get("/examination-records", response_model=list[dict[str, Any]])
def examination_records(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> list[dict[str, Any]]:
    return store.list_examinations()


@router.post("/save-visit")
def save_visit(
    body: SaveVisitRequest,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, Any]:
    soap = {
        "subjective": body.soap_summary.subjective,
        "objective": body.soap_summary.objective,
        "assessment": body.soap_summary.assessment,
        "plan": body.soap_summary.plan,
    }
    try:
        return store.save_visit_encounter(
            visit_id=body.visit_id,
            patient_id=body.patient_id,
            transcript=body.transcript,
            soap=soap,
            prescriptions=body.prescriptions,
            doctor_notes=body.doctor_notes,
            doctor_staff_id=user.staff_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
