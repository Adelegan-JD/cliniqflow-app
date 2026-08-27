from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, CurrentUser, require_roles
from app.repositories import store
from app.schemas.clinical_forms import ClinicalFormResponseCreate, ClinicalFormTemplateCreate

router = APIRouter(prefix="/clinical-forms", tags=["clinical forms"])


@router.get("/templates", response_model=list[dict[str, Any]])
def list_templates(
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> list[dict[str, Any]]:
    return store.list_clinical_form_templates()


@router.post("/templates", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_template(
    body: ClinicalFormTemplateCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN))],
) -> dict[str, Any]:
    return store.create_clinical_form_template(body.model_dump(), user.staff_id)


@router.post("/responses", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_response(
    body: ClinicalFormResponseCreate,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> dict[str, Any]:
    row = store.create_clinical_form_response(body.model_dump(), user.staff_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template, patient, or encounter was not found")
    return row


@router.get("/responses/patient/{patient_id}", response_model=list[dict[str, Any]])
def list_patient_responses(
    patient_id: str,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE))],
) -> list[dict[str, Any]]:
    return store.list_clinical_form_responses(patient_id)
