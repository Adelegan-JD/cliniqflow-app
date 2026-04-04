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
    return ai_engine_client.post_json(
        "/internal/rag/guidelines",
        body.model_dump(exclude_none=True),
    )


@router_ai.post("/dose-check")
def dose_check(
    body: DoseCheckBody,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, Any]:
    payload = body.model_dump()
    return ai_engine_client.post_json("/internal/rag/dose-check", payload)


@router_nlp.post("/vitals-urgency")
def vitals_urgency(
    body: VitalsUrgencyRequest,
    _user: Annotated[CurrentUser, Depends(require_roles(ROLE_NURSE))],
) -> dict[str, Any]:
    return ai_engine_client.post_json(
        "/internal/nlp/vitals-urgency",
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
    return ai_engine_client.post_multipart("/internal/asr/transcribe-chunk", files, data)
