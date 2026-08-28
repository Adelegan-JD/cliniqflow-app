"""
api/asr.py
-----------
ASR (Automatic Speech Recognition) API router.
Mounted at /asr in main.py

Endpoints:
  GET  /asr/health      — model load status
  POST /asr/transcribe  — upload audio, get diarized transcript
"""

import logging
import os
import tempfile
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List

from app.asr.asr_service import ASRService

logger = logging.getLogger(__name__)

router  = APIRouter(prefix="/asr", tags=["ASR"])
limiter = Limiter(key_func=get_remote_address)

SAMPLE_RATE  = 16000
MAX_FILE_MB  = 50
ALLOWED_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mpeg", "audio/mp4", "audio/webm",
    "audio/ogg", "application/octet-stream",
}


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class TranscriptSegment(BaseModel):
    speaker:     str
    start:       float
    end:         float
    translation: str

class TranscribeResponse(BaseModel):
    session_id:       str
    segments:         List[TranscriptSegment]
    transcript:       str
    duration_seconds: float

class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    device:       str
    diarization_enabled: bool


# ── Audio loader ───────────────────────────────────────────────────────────────

def _save_audio_upload(file: UploadFile) -> tuple[str, int]:
    """Validate an upload and save it temporarily for the ASR decoder."""
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    contents = file.file.read()
    if len(contents) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_MB} MB limit")

    suffix = os.path.splitext(file.filename or "recording.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    return tmp_path, len(contents)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, summary="ASR health check")
async def asr_health(request: Request):
    """Returns the load state of the ASR models."""
    mm = request.app.state.model_manager
    return HealthResponse(
        status="ready" if mm.model_loaded else "loading",
        model_loaded=mm.model_loaded,
        device=mm.device or "unknown",
        diarization_enabled=mm.diarization_enabled,
    )


@router.post(
    "/transcribe", #added the asr prefix
    response_model=TranscribeResponse,
    summary="Transcribe + diarize an audio file",
)
@limiter.limit("30/minute")
async def transcribe(
    request: Request,
    file: UploadFile = File(..., description="Audio file (wav, mp3, mp4, webm, ogg)"),
):
    """
    Upload an audio file and receive a speaker-diarized English transcript.
    - Accepts wav, mp3, mp4, webm, ogg  |  Max: 50 MB
    - Returns per-speaker segments sorted by start time
    """
    mm = request.app.state.model_manager
    service = ASRService(mm)   # inject the shared ModelManager

    if not service.is_ready():
        raise HTTPException(status_code=503, detail="Models still loading, try again shortly")

    session_id = str(uuid.uuid4())
    logger.info(f"[{session_id}] Transcription request — file: {file.filename}")
    t0 = time.time()

    audio_path, _size = _save_audio_upload(file)
    try:
        result = service.transcribe_and_format(audio_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=f"Could not transcribe audio: {exc}") from exc
    finally:
        os.unlink(audio_path)
    duration = round(max((segment["end"] for segment in result["segments"]), default=0.0), 2)

    logger.info(
        f"[{session_id}] Done — {len(result['segments'])} segments, "
        f"{duration}s audio, {round(time.time()-t0, 2)}s processing"
    )

    return TranscribeResponse(
        session_id=session_id,
        segments=[TranscriptSegment(**s) for s in result["segments"]],
        transcript=result["conversation"],
        duration_seconds=duration,
    )
