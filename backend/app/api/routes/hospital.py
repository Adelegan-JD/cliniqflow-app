"""Hospital configuration and inpatient admission APIs.

Payment collection is intentionally excluded until the invoice/payment workflow
has dual-control approval and provider-webhook verification.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, CurrentUser, require_roles
from app.repositories import store
from app.schemas.hospital import (
    AdmissionCreate, BedAssignmentCreate, BedCreate, DepartmentCreate,
    DischargeCreate, LocationCreate, NursingObservationCreate,
)

router = APIRouter(prefix="/hospital", tags=["hospital"])


STARTER_DEPARTMENTS = [
    ("GENMED", "General Medicine", "Internal Medicine"),
    ("PAEDS", "Paediatrics", "Paediatrics"),
    ("OBGYN", "Obstetrics and Gynaecology", "Obstetrics and Gynaecology"),
    ("SURG", "Surgery", "General Surgery"),
    ("NEURO", "Neurology", "Neurology"),
    ("NEPHRO", "Nephrology", "Nephrology"),
    ("OPHTH", "Ophthalmology", "Ophthalmology"),
    ("DERM", "Dermatology", "Dermatology"),
    ("ORTHO", "Orthopaedics", "Orthopaedics"),
    ("ENT", "Ear, Nose and Throat", "Otolaryngology"),
    ("PSYCH", "Mental Health", "Psychiatry"),
    ("DENT", "Dental", "Dentistry"),
    ("CARDIO", "Cardiology", "Cardiology"),
    ("ONCOL", "Oncology", "Oncology"),
    ("HAEM", "Haematology", "Haematology"),
    ("RAD", "Radiology", "Radiology"),
    ("FAMMED", "Family Medicine", "Family Medicine"),
    ("REHAB", "Rehabilitation", "Physiotherapy and Occupational Therapy"),
    ("ID", "Infectious Diseases", "Infectious Diseases"),
    ("RENAL", "Renal Services", "Dialysis and Renal Care"),
    ("ANAES", "Anaesthesia and Critical Care", "Anaesthesia and Critical Care"),
]

STARTER_LOCATIONS = [
    ("GEN-OPD", "General Outpatient Clinic", "outpatient_clinic", "GENMED"),
    ("PAEDS-OPD", "Paediatric Outpatient Clinic", "outpatient_clinic", "PAEDS"),
    ("ANC", "Antenatal Clinic", "outpatient_clinic", "OBGYN"),
    ("GYN-OPD", "Gynaecology Clinic", "outpatient_clinic", "OBGYN"),
    ("SURG-OPD", "Surgical Outpatient Clinic", "outpatient_clinic", "SURG"),
    ("NEURO-OPD", "Neurology Clinic", "outpatient_clinic", "NEURO"),
    ("NEPHRO-OPD", "Nephrology Clinic", "outpatient_clinic", "NEPHRO"),
    ("OPHTH-OPD", "Ophthalmology Clinic", "outpatient_clinic", "OPHTH"),
    ("DERM-OPD", "Dermatology Clinic", "outpatient_clinic", "DERM"),
    ("ORTHO-OPD", "Orthopaedic Clinic", "outpatient_clinic", "ORTHO"),
    ("ENT-OPD", "ENT Clinic", "outpatient_clinic", "ENT"),
    ("DENT-OPD", "Dental Clinic", "outpatient_clinic", "DENT"),
    ("CARDIO-OPD", "Cardiology Clinic", "outpatient_clinic", "CARDIO"),
    ("ONCOL-OPD", "Oncology Clinic", "outpatient_clinic", "ONCOL"),
    ("HAEM-OPD", "Haematology Clinic", "outpatient_clinic", "HAEM"),
    ("RAD-OPD", "Radiology Clinic", "outpatient_clinic", "RAD"),
    ("FAMMED-OPD", "Family Medicine Clinic", "outpatient_clinic", "FAMMED"),
    ("PSYCH-OPD", "Mental Health Clinic", "outpatient_clinic", "PSYCH"),
    ("REHAB-OPD", "Physiotherapy and Rehabilitation Clinic", "outpatient_clinic", "REHAB"),
    ("ID-OPD", "Infectious Diseases Clinic", "outpatient_clinic", "ID"),
    ("NHIA-OPD", "NHIA / Insurance Clinic", "outpatient_clinic", None),
    ("ED", "Emergency Unit", "emergency_unit", None),
    ("PAEDS-ER", "Children Emergency Unit", "emergency_unit", "PAEDS"),
    ("OBGYN-ER", "Gynaecology Emergency Unit", "emergency_unit", "OBGYN"),
    ("MED-M-WARD", "Male Medical Ward", "ward", "GENMED"),
    ("MED-F-WARD", "Female Medical Ward", "ward", "GENMED"),
    ("PAEDS-WARD", "Paediatric Ward", "ward", "PAEDS"),
    ("NEONATAL", "Neonatal Ward", "ward", "PAEDS"),
    ("LABOUR", "Labour and Delivery Ward", "ward", "OBGYN"),
    ("POSTNATAL", "Postnatal Ward", "ward", "OBGYN"),
    ("SURG-M-WARD", "Male Surgical Ward", "ward", "SURG"),
    ("SURG-F-WARD", "Female Surgical Ward", "ward", "SURG"),
    ("ORTHO-WARD", "Orthopaedic Ward", "ward", "ORTHO"),
    ("CARDIO-M-WARD", "Male Cardiology Ward", "ward", "CARDIO"),
    ("CARDIO-F-WARD", "Female Cardiology Ward", "ward", "CARDIO"),
    ("RENAL-M-WARD", "Male Renal Ward", "ward", "RENAL"),
    ("RENAL-F-WARD", "Female Renal Ward", "ward", "RENAL"),
    ("DIALYSIS", "Dialysis Unit", "ward", "RENAL"),
    ("ICU", "Intensive Care Unit", "ward", None),
    ("HDU", "High Dependency Unit", "ward", None),
    ("ISO-1", "Isolation Ward 1", "ward", "ID"),
    ("ISO-2", "Isolation Ward 2", "ward", "ID"),
    ("THEATRE", "Main Operating Theatre", "theatre", "SURG"),
    ("LAB", "Laboratory", "laboratory", None),
    ("PHARM", "Pharmacy", "pharmacy", None),
]


@router.get("/departments", response_model=list[dict[str, Any]])
def list_departments(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> list[dict[str, Any]]:
    return store.list_departments()


@router.post("/departments", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_department(
    body: DepartmentCreate,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, Any]:
    return store.create_department(body.model_dump())


@router.post("/starter-catalogue", response_model=dict[str, int], status_code=status.HTTP_201_CREATED)
def load_starter_catalogue(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, int]:
    return store.load_starter_catalogue(STARTER_DEPARTMENTS, STARTER_LOCATIONS)


@router.get("/locations", response_model=list[dict[str, Any]])
def list_locations(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> list[dict[str, Any]]:
    return store.list_locations()


@router.post("/locations", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_location(
    body: LocationCreate,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, Any]:
    return store.create_location(body.model_dump())


@router.get("/beds", response_model=list[dict[str, Any]])
def list_beds(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> list[dict[str, Any]]:
    return store.list_beds()


@router.post("/beds", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_bed(
    body: BedCreate,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, Any]:
    return store.create_bed(body.model_dump())


@router.get("/admissions", response_model=list[dict[str, Any]])
def list_admissions(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> list[dict[str, Any]]:
    return store.list_admissions()


@router.post("/admissions", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_admission(
    body: AdmissionCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR))],
) -> dict[str, Any]:
    row = store.create_admission(body.model_dump(), created_by=user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return row


@router.post("/admissions/{admission_id}/bed-assignments", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def assign_bed(
    admission_id: str,
    body: BedAssignmentCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR))],
) -> dict[str, Any]:
    row = store.assign_bed(admission_id, body.bed_id, user.staff_id, body.reason)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admission is inactive, bed is unavailable, or record was not found")
    return row


@router.post("/admissions/{admission_id}/transfer", response_model=dict[str, Any])
def transfer_bed(
    admission_id: str,
    body: BedAssignmentCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR))],
) -> dict[str, Any]:
    row = store.assign_bed(admission_id, body.bed_id, user.staff_id, body.reason or "transfer")
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transfer could not be completed")
    return row


@router.post("/admissions/{admission_id}/discharge", response_model=dict[str, Any])
def discharge_patient(
    admission_id: str,
    body: DischargeCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR))],
) -> dict[str, Any]:
    summary = store.get_discharge_summary(admission_id)
    if not summary or summary.get("status") != "final":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A final discharge summary is required before discharge")
    row = store.discharge_admission(admission_id, body.discharge_disposition, user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admission is inactive or was not found")
    return row


@router.get("/admissions/{admission_id}/observations", response_model=list[dict[str, Any]])
def list_observations(
    admission_id: str,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> list[dict[str, Any]]:
    return store.list_nursing_observations(admission_id)


@router.post("/admissions/{admission_id}/observations", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def record_observation(
    admission_id: str,
    body: NursingObservationCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> dict[str, Any]:
    row = store.record_nursing_observation(admission_id, body.model_dump(exclude_none=True), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admission is inactive or was not found")
    return row
