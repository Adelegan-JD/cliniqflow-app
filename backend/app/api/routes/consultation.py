"""
Consultation session API routes.
Handles session creation, transcription upload, and completion.
"""
from typing import Annotated, Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from pydantic import BaseModel

from app.core.security import (
    ROLE_DOCTOR,
    CurrentUser,
    get_current_user,
    require_roles,
)
from app.repositories.session_store import get_session_store
from app.schemas.consultation import (
    ConsultationSession,
    StartConsultationRequest,
    StartConsultationResponse,
    EndConsultationRequest,
)
from app.services import ai_engine_client

router = APIRouter(prefix="/consultation", tags=["consultation-session"])
session_store = get_session_store()


@router.post("/session/start", response_model=StartConsultationResponse)
def start_consultation_session(
    body: StartConsultationRequest,
    user: Annotated[CurrentUser, Depends(require_roles(ROLE_DOCTOR))],
) -> dict[str, Any]:
    """
    Initialize a new consultation recording session.
    
    Generates unique session_id with format: pid/visit_id/session_id
    
    Returns session details for frontend to use during recording.
    """
    session_id, session_path = session_store.create_session(
        patient_id=body.patient_id,
        visit_id=body.visit_id,
        doctor_id=user.id,  # Use authenticated doctor's ID
    )
    
    session = session_store.get_session(session_id)
    
    return StartConsultationResponse(
        session_id=session_id,
        patient_id=body.patient_id,
        visit_id=body.visit_id,
        session_path=session_path,
        started_at=session.started_at,
    )


@router.post("/session/{session_id}/transcribe")
async def upload_and_transcribe(
    session_id: str,
    file: UploadFile = File(...),
    user: Annotated[CurrentUser, Depends(get_current_user)] = None,
) -> dict[str, Any]:
    """
    Upload audio recording for transcription via AI engine.
    
    - Receives audio chunk from frontend
    - Proxies to AI engine Whisper for transcription + diarization
    - Stores result in session
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Read audio file
    content = await file.read()
    files = {
        "file": (
            file.filename or "recording.webm",
            content,
            file.content_type or "audio/webm",
        )
    }
    
    # Send to AI engine for transcription
    try:
        result = ai_engine_client.post_multipart(
            "/asr/transcribe",
            files,
            {},
            timeout=600.0,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI engine transcription failed: {str(e)}",
        )
    
    # Store transcription in session
    session_store.update_session(
        session_id=session_id,
        transcript=result.get("transcript", ""),
        transcript_segments=result.get("segments", []),
        duration_seconds=result.get("duration_seconds", 0),
    )
    
    return {
        "session_id": session_id,
        "transcript": result.get("transcript", ""),
        "segments": result.get("segments", []),
        "duration_seconds": result.get("duration_seconds", 0),
        "status": "transcribed",
    }


@router.post("/session/{session_id}/end")
def end_consultation_session(
    session_id: str,
    body: EndConsultationRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)] = None,
) -> ConsultationSession:
    """
    Finalize a consultation session.
    
    Marks as completed and triggers downstream processing (SOAP generation, storage).
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Update with final data if provided
    if body.transcript or body.transcript_segments or body.duration_seconds:
        session_store.update_session(
            session_id=session_id,
            transcript=body.transcript,
            transcript_segments=body.transcript_segments,
            duration_seconds=body.duration_seconds,
        )
    
    # Mark as completed
    completed_session = session_store.end_session(session_id)
    
    return completed_session


@router.get("/session/{session_id}", response_model=ConsultationSession)
def get_consultation_session(
    session_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)] = None,
) -> ConsultationSession:
    """Retrieve current consultation session details."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    return session
