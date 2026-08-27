from typing import Annotated, Any

from app.schemas.ai_contracts import VitalsUrgencyRequest
from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field

from app.core.security import (
    ROLE_DOCTOR,
    ROLE_NURSE,
    CurrentUser,
    get_current_user,
    require_roles,
)
from app.services import ai_engine_client
from app.repositories import store

router_ai = APIRouter(prefix="/ai", tags=["ai-orchestration"])
router_nlp = APIRouter(prefix="/nlp", tags=["nlp-orchestration"])
router_asr = APIRouter(tags=["asr-orchestration"])


class GuidelinesBody(BaseModel):
    query: str = Field(min_length=1)
    condition: str | None = None


class DoseCheckBody(BaseModel):
    visit_id: str | None = None
    drug: str = Field(min_length=1)
    age_years: int = Field(ge=0, le=120)
    weight_kg: float = Field(gt=0, le=300)
    frequency_per_day: int = Field(ge=1, le=24)
    chosen_dose_mg_per_day: int = Field(ge=1)


@router_ai.post("/guidelines")
def guidelines_search(
    body: GuidelinesBody,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, Any]:
    # The AI service exposes evidence retrieval, not a free-form guideline
    # generator.  Keep the original condition as useful retrieval context.
    query = " ".join(part for part in (body.condition, body.query) if part)
    return ai_engine_client.post_json("/rag/retrieve", {"query": query})


@router_ai.post("/dose-check")
def dose_check(
    body: DoseCheckBody,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, Any]:
    # The UI collects a *total daily* dose.  The validator needs a single dose
    # plus frequency, so translate the contract explicitly at this boundary.
    single_dose_mg = body.chosen_dose_mg_per_day / body.frequency_per_day
    result = ai_engine_client.post_json(
        "/rag/validate-dose",
        {
            "drug_name": body.drug,
            "dose_mg": single_dose_mg,
            "frequency_per_day": body.frequency_per_day,
            "patient_weight_kg": body.weight_kg,
            "patient_age_years": body.age_years,
        },
    )

    # Preserve the existing frontend contract while the newer prescribing UI
    # is being completed.  A clinician still decides whether to prescribe and
    # must provide an override reason for a non-safe result.
    safe = result.get("safety_level") == "safe"
    min_mgkg = result.get("recommended_min_mgkg")
    max_mgkg = result.get("recommended_max_mgkg")
    response = {
        "safe": safe,
        "warnings": result.get("reasons", []),
        "recommended_range_mg_per_day": {
            "min": min_mgkg * body.weight_kg if min_mgkg is not None else None,
            "max": max_mgkg * body.weight_kg if max_mgkg is not None else None,
        },
        "max_mg_per_day": result.get("max_daily_mg"),
        "allow_override": not safe,
        "assessment": result,
        "evidence": result.get("evidence", []),
    }
    record = store.record_dosage_check(
        body.visit_id, _user.staff_id, body.model_dump(), result
    )
    response["check_id"] = record.get("id") if record else None
    return response


@router_nlp.post("/vitals-urgency")
def vitals_urgency(
    body: VitalsUrgencyRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> dict[str, Any]:
    return ai_engine_client.post_json(
        "/nlp/vitals-urgency",    #removed the internal prefix
        body.model_dump(exclude_none=True),
    )


@router_asr.post("/translate/chunk")
async def translate_chunk(
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    file: UploadFile | None = File(None),
    session_id: str | None = Form(None),
    chunk_index: str | None = Form(None),
) -> dict[str, Any]:
    """Proxies audio to the AI ASR endpoint."""
    if file is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file")
    content = await file.read()
    files = {"file": (file.filename or "chunk.webm", content, file.content_type or "application/octet-stream")}
    data = {
        "session_id": session_id or "",
        "chunk_index": chunk_index or "0",
    }
    return ai_engine_client.post_multipart("/asr/transcribe", files, data) #removed the internals as well
