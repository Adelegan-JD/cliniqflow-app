from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import ROLE_NURSE, CurrentUser, require_roles
from app.repositories.memory_store import store

router = APIRouter(prefix="/nurse", tags=["nurse"])


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


@router.post("/triage")
def submit_triage(
    body: TriageSubmitRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> dict[str, Any]:
    ev = store.save_triage(
        visit_id=body.visit_id,
        patient_id=body.patient_id,
        vitals=body.vitals,
        urgency=body.urgency_level,
    )
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit or patient mismatch",
        )
    return ev
