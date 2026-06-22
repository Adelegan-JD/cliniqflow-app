"""
Consultation session schemas for recording, transcription, and SOAP generation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ConsultationSession(BaseModel):
    """Active consultation session with recording metadata."""
    session_id: str = Field(..., description="Unique session identifier")
    patient_id: str = Field(..., description="Patient ID (pid)")
    visit_id: str = Field(..., description="Visit ID")
    doctor_id: str = Field(..., description="Doctor/staff initiating session")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    transcript_raw: Optional[str] = None
    transcript_segments: Optional[list] = None  # Speaker-diarized segments
    status: str = Field(default="active", description="active | completed | archived")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456",
                "patient_id": "P001",
                "visit_id": "V001",
                "doctor_id": "D001",
                "status": "active"
            }
        }


class StartConsultationRequest(BaseModel):
    """Request to start a new consultation session."""
    patient_id: str = Field(..., description="Patient ID")
    visit_id: str = Field(..., description="Visit ID")
    doctor_id: str = Field(..., description="Doctor/staff ID")


class StartConsultationResponse(BaseModel):
    """Response containing new session details."""
    session_id: str
    patient_id: str
    visit_id: str
    session_path: str  # Format: pid/visit_id/session_id
    started_at: datetime


class EndConsultationRequest(BaseModel):
    """Request to finalize consultation session."""
    transcript: Optional[str] = None
    transcript_segments: Optional[list] = None
    duration_seconds: Optional[float] = None


class TranscriptionResult(BaseModel):
    """Result from AI engine transcription."""
    session_id: str
    transcript: str
    segments: list = Field(default=[], description="Speaker-diarized segments")
    duration_seconds: float
    confidence_score: Optional[float] = None
