from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import (
    ROLE_ADMIN,
    ROLE_DOCTOR,
    ROLE_NURSE,
    ROLE_RECORD_OFFICER,
    CurrentUser,
    require_roles,
)
from app.repositories.memory_store import store

router = APIRouter(prefix="/record-officer", tags=["record-officer"])


class RegisterPatientBody(BaseModel):
    firstName: str
    lastName: str
    otherNames: str | None = None
    dob: str
    gender: str
    civilStatus: str | None = None
    religion: str | None = None
    tribe: str | None = None
    nationality: str | None = None
    phone: str
    altPhone: str | None = None
    email: str | None = None
    address: str
    state: str | None = None
    lga: str | None = None
    nin: str | None = None
    nhisNumber: str | None = None
    militaryNumber: str | None = None
    education: str | None = None
    occupation: str | None = None
    nokName: str
    nokRelationship: str
    nokPhone: str
    nokAddress: str | None = None


class CreateVisitBody(BaseModel):
    patient_id: str
    reason_for_visit: str | None = None
    department: str | None = None


@router.get("/dashboard")
def record_officer_dashboard(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_RECORD_OFFICER, ROLE_ADMIN))],
) -> dict[str, Any]:
    return store.record_officer_dashboard()


@router.get("/patients", response_model=list[dict[str, Any]])
def list_patients(
    _user: Annotated[
        CurrentUser,
        Depends(require_roles(ROLE_RECORD_OFFICER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN)),
    ],
    search: str | None = Query(None),
) -> list[dict[str, Any]]:
    rows = store.list_patients(search)
    return [
        {
            "id": p["id"],
            "pid": p.get("pid"),
            "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
            "phone": p.get("phone"),
            "dob": p.get("dob"),
            "gender": p.get("gender"),
        }
        for p in rows
    ]


@router.get("/patients/search", response_model=list[dict[str, Any]])
def search_patients(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_RECORD_OFFICER, ROLE_ADMIN))],
    q: str = Query(..., min_length=1),
    search_by: str = Query("pid", pattern="^(pid|phone|nameDob)$"),
) -> list[dict[str, Any]]:
    return store.search_patients(q, search_by)


@router.post("/register-patient")
def register_patient(
    body: RegisterPatientBody,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_RECORD_OFFICER))],
) -> dict[str, Any]:
    data = body.model_dump()
    row = store.register_patient(data)
    return {"pid": row["pid"], "id": row["id"], **row}


@router.post("/visits")
def create_visit(
    body: CreateVisitBody,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_RECORD_OFFICER))],
) -> dict[str, Any]:
    row = store.create_visit(
        patient_id=body.patient_id,
        reason_for_visit=body.reason_for_visit,
        department=body.department,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
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
