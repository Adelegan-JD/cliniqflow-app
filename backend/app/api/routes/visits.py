from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import (
    ROLE_ADMIN,
    ROLE_DOCTOR,
    ROLE_NURSE,
    ROLE_RECORD_OFFICER,
    CurrentUser,
    require_roles,
)
from app.repositories import store
from app.schemas.workflows import CreateVisitBody
from app.services import ai_engine_client

router = APIRouter(prefix="/visits", tags=["visits"])


class DoctorConversationRequest(BaseModel):
    transcript: str = Field(min_length=1)
    patient_age: str | None = None
    patient_sex: str | None = None
    triage_vitals: dict[str, Any] | None = None


@router.get("", response_model=list[dict[str, Any]])
def list_visits(
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN, ROLE_RECORD_OFFICER)),
    ],
) -> list[dict[str, Any]]:
    return store.list_visits_values()


@router.post("", response_model=dict[str, Any])
def create_visit(
    body: CreateVisitBody,
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_RECORD_OFFICER, ROLE_ADMIN)),
    ],
) -> dict[str, Any]:
    """Same behaviour as POST /record-officer/visits for REST-style clients."""
    row = store.create_visit(
        patient_id=body.patient_id,
        reason_for_visit=body.reason_for_visit,
        department=body.department,
        checked_in_by=_user.staff_id,
    )
    if not row:
        # Check if patient exists to distinguish between not found vs already has active visit
        patient = store.get_patient(body.patient_id)
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient already has an active visit. Please complete the current visit before creating a new one."
            )
    created = row["created_at"]
    return {
        "visit_id": row["visit_id"],
        "patient_id": row["patient_id"],
        "patient_name": row["patient_name"],
        "visit_date": created[:10] if created else None,
        "visit_time": created[11:16] if created and len(created) >= 16 else None,
        "visit_status": row["visit_status"],
        "triage_status": row["triage_status"],
        "created_at": created,
    }


@router.get("/{visit_id}", response_model=dict[str, Any])
def get_visit(
    visit_id: str,
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN, ROLE_RECORD_OFFICER)),
    ],
) -> dict[str, Any]:
    v = store.get_visit(visit_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return v


@router.post("/{visit_id}/doctor-conversation", response_model=dict[str, Any])
def doctor_conversation(
    visit_id: str,
    body: DoctorConversationRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, Any]:
    payload = {
        "transcript": body.transcript,
        "patient_age": body.patient_age,
        "patient_sex": body.patient_sex,
        "triage_vitals": body.triage_vitals,
    }
    data = ai_engine_client.post_json("/internal/nlp/soap-from-transcript", payload)
    return {"visit_id": visit_id, **data}
