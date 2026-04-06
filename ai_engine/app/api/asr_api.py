"""
api/asr_api.py
---------------
ASR API router — transcription + conversation session management.
Mounted at /asr in main.py

Endpoints:
  GET  /asr/health                        — model load status
  POST /asr/transcribe                    — transcribe a single audio file
  POST /asr/transcribe/{session_id}       — add a chunk to an existing session
  GET  /asr/conversation/{session_id}     — retrieve full session transcript
  DELETE /asr/conversation/{session_id}  — end session and return final transcript
"""

import logging
import os
import tempfile
import time
import uuid
from collections import defaultdict
from typing import List, Optional

import librosa
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# ── Routers ────────────────────────────────────────────────────────────────────
router               = APIRouter(prefix="/asr",          tags=["ASR"])
conversation_router  = APIRouter(prefix="/asr/conversation", tags=["Conversation"])

limiter = Limiter(key_func=get_remote_address)

SAMPLE_RATE   = 16000
MAX_FILE_MB   = 50
ALLOWED_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mpeg", "audio/mp4", "audio/webm",
    "audio/ogg", "application/octet-stream",
}

# ── Session store (in-memory) ──────────────────────────────────────────────────
# { session_id: [ {chunk_index, segments, conversation}, ... ] }
session_store: dict = defaultdict(list)


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class TranscriptSegment(BaseModel):
    speaker:     str
    start:       float
    end:         float
    translation: str

class TranscribeResponse(BaseModel):
    session_id:       str
    chunk_index:      int
    segments:         List[TranscriptSegment]
    transcript:       str
    duration_seconds: float

class ConversationResponse(BaseModel):
    session_id:        str
    total_chunks:      int
    all_segments:      List[TranscriptSegment]
    full_conversation: str

class EndConversationResponse(BaseModel):
    status:            str
    session_id:        str
    total_chunks:      int
    full_conversation: str

class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    device:       str


# ── Audio loader ───────────────────────────────────────────────────────────────

def _load_audio(file: UploadFile) -> np.ndarray:
    """Validate, read, and resample uploaded audio to mono float32 at 16 kHz."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    contents = file.file.read()
    if len(contents) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_MB} MB limit")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        audio, _ = librosa.load(tmp_path, sr=SAMPLE_RATE, mono=True)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not decode audio: {e}")
    finally:
        os.unlink(tmp_path)

    return audio


def _run_transcription(file: UploadFile, request: Request):
    """Shared transcription logic used by both transcribe endpoints."""
    from app.asr.asr_service import ASRService
    mm      = request.app.state.model_manager
    service = ASRService(mm)

    if not service.is_ready():
        raise HTTPException(status_code=503, detail="Models still loading, try again shortly")

    t0       = time.time()
    audio    = _load_audio(file)
    duration = round(len(audio) / SAMPLE_RATE, 2)
    result   = service.transcribe_and_format(audio)

    logger.info(
        f"Done — {len(result['segments'])} segments, "
        f"{duration}s audio, {round(time.time()-t0, 2)}s processing"
    )
    return result, duration


# ── ASR Routes ─────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, summary="ASR health check")
async def asr_health(request: Request):
    """Returns the load state of the ASR models."""
    mm = request.app.state.model_manager
    return HealthResponse(
        status="ready" if mm.model_loaded else "loading",
        model_loaded=mm.model_loaded,
        device=mm.device or "unknown",
    )


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe a single audio file (creates new session)",
)
@limiter.limit("10/minute")
async def transcribe(
    request: Request,
    file: UploadFile = File(..., description="Audio file (wav, mp3, mp4, webm, ogg)"),
):
    """
    Upload an audio file → get a speaker-diarized English transcript.
    Creates a new session automatically. Use the returned session_id
    to add more chunks or retrieve the full conversation.
    """
    session_id  = str(uuid.uuid4())
    chunk_index = 0
    logger.info(f"[{session_id}] New session — file: {file.filename}")

    result, duration = _run_transcription(file, request)

    # Store chunk in session
    session_store[session_id].append({
        "chunk_index":  chunk_index,
        "segments":     result["segments"],
        "conversation": result["conversation"],
    })

    return TranscribeResponse(
        session_id=session_id,
        chunk_index=chunk_index,
        segments=[TranscriptSegment(**s) for s in result["segments"]],
        transcript=result["conversation"],
        duration_seconds=duration,
    )


@router.post(
    "/transcribe/{session_id}",
    response_model=TranscribeResponse,
    summary="Add a chunk to an existing session",
)
@limiter.limit("10/minute")
async def transcribe_chunk(
    session_id: str,
    request:    Request,
    file: UploadFile = File(..., description="Next audio chunk"),
):
    """
    Upload the next audio chunk for an existing session.
    Each chunk is transcribed independently and appended to the session.
    """
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Start with POST /asr/transcribe")

    chunk_index = len(session_store[session_id])
    logger.info(f"[{session_id}] Chunk {chunk_index} — file: {file.filename}")

    result, duration = _run_transcription(file, request)

    session_store[session_id].append({
        "chunk_index":  chunk_index,
        "segments":     result["segments"],
        "conversation": result["conversation"],
    })

    return TranscribeResponse(
        session_id=session_id,
        chunk_index=chunk_index,
        segments=[TranscriptSegment(**s) for s in result["segments"]],
        transcript=result["conversation"],
        duration_seconds=duration,
    )


# ── Conversation Routes ────────────────────────────────────────────────────────

@conversation_router.get(
    "/{session_id}",
    response_model=ConversationResponse,
    summary="Get full conversation transcript for a session",
)
async def get_conversation(session_id: str, request: Request):
    """
    Retrieve all chunks for a session assembled into one full transcript.
    Chunks are labelled [Chunk 0], [Chunk 1]... to show where each recording begins.
    """
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found.")

    chunks       = [c for c in session_store[session_id] if c is not None]
    full_text    = "\n\n".join([f"[Chunk {c['chunk_index']}]\n{c['conversation']}" for c in chunks])
    all_segments = [seg for c in chunks for seg in c["segments"]]

    return ConversationResponse(
        session_id=session_id,
        total_chunks=len(chunks),
        all_segments=[TranscriptSegment(**s) for s in all_segments],
        full_conversation=full_text,
    )


@conversation_router.delete(
    "/{session_id}",
    response_model=EndConversationResponse,
    summary="End a session and return the complete final transcript",
)
async def end_conversation(session_id: str, request: Request):
    """
    End the session — assembles the full transcript, clears it from memory,
    and returns the complete conversation. Call this when the consultation is done.
    """
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found.")

    chunks    = [c for c in session_store[session_id] if c is not None]
    full_text = "\n\n".join([f"[Chunk {c['chunk_index']}]\n{c['conversation']}" for c in chunks])

    del session_store[session_id]
    logger.info(f"Session {session_id} ended | {len(chunks)} chunks | {len(full_text)} chars")

    return EndConversationResponse(
        status="ended",
        session_id=session_id,
        total_chunks=len(chunks),
        full_conversation=full_text,
    )
