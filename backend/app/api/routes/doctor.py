from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import ROLE_DOCTOR, CurrentUser, require_roles
from app.repositories.memory_store import store

router = APIRouter(prefix="/doctor", tags=["doctor"])


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


@router.get("/examination-records", response_model=list[dict[str, Any]])
def examination_records(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> list[dict[str, Any]]:
    return store.list_examinations()


@router.post("/save-visit")
def save_visit(
    body: SaveVisitRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, Any]:
    soap = {
        "subjective": body.soap_summary.subjective,
        "objective": body.soap_summary.objective,
        "assessment": body.soap_summary.assessment,
        "plan": body.soap_summary.plan,
    }
    return store.save_visit_encounter(
        visit_id=body.visit_id,
        patient_id=body.patient_id,
        transcript=body.transcript,
        soap=soap,
        prescriptions=body.prescriptions,
        doctor_notes=body.doctor_notes,
    )
