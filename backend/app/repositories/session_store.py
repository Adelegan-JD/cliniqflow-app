"""
In-memory and persistent session management for consultation recordings.
"""
import uuid
from datetime import datetime
from typing import Any, Optional
from app.schemas.consultation import ConsultationSession


class SessionStore:
    """In-memory store for active consultation sessions.
    
    In production, this would be backed by Redis or database.
    For now, uses in-memory dict with format: session_id -> ConsultationSession
    """
    
    def __init__(self):
        self._sessions: dict[str, ConsultationSession] = {}
    
    def create_session(
        self,
        patient_id: str,
        visit_id: str,
        doctor_id: str,
    ) -> tuple[str, str]:
        """
        Create and store a new consultation session.
        
        Returns:
            (session_id, session_path) where session_path = f"{patient_id}/{visit_id}/{session_id}"
        """
        session_id = str(uuid.uuid4())
        session_path = f"{patient_id}/{visit_id}/{session_id}"
        
        session = ConsultationSession(
            session_id=session_id,
            patient_id=patient_id,
            visit_id=visit_id,
            doctor_id=doctor_id,
            status="active"
        )
        
        self._sessions[session_id] = session
        return session_id, session_path
    
    def get_session(self, session_id: str) -> Optional[ConsultationSession]:
        """Retrieve an active session by ID."""
        return self._sessions.get(session_id)
    
    def update_session(
        self,
        session_id: str,
        transcript: Optional[str] = None,
        transcript_segments: Optional[list] = None,
        duration_seconds: Optional[float] = None,
    ) -> Optional[ConsultationSession]:
        """Update session with transcription results."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        if transcript:
            session.transcript_raw = transcript
        if transcript_segments:
            session.transcript_segments = transcript_segments
        if duration_seconds is not None:
            session.duration_seconds = duration_seconds
        
        self._sessions[session_id] = session
        return session
    
    def end_session(self, session_id: str) -> Optional[ConsultationSession]:
        """Mark session as completed."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        session.ended_at = datetime.utcnow()
        session.status = "completed"
        self._sessions[session_id] = session
        return session
    
    def get_patient_sessions(self, patient_id: str) -> list[ConsultationSession]:
        """Get all sessions for a patient."""
        return [
            s for s in self._sessions.values()
            if s.patient_id == patient_id
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session (e.g., for archival)."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# Global session store instance
_session_store = SessionStore()


def get_session_store() -> SessionStore:
    """Get the global session store."""
    return _session_store
