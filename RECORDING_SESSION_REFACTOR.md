# Recording Session Refactoring - Integration Guide

## Overview

The recording session has been refactored to support:

1. **Session Management**: Unique session IDs generated on consultation start
2. **AI Engine Integration**: Whisper transcription with speaker diarization
3. **Structured Path**: Session format `pid/visit_id/session_id`
4. **Full Workflow**: Recording → Transcription → SOAP generation

## Architecture

### Backend Flow

```
Frontend Start Consultation
    ↓
POST /consultation/session/start
    ↓ (Backend)
Create ConsultationSession
Generate session_id (UUID)
Build session_path (pid/visit_id/session_id)
    ↓
Return session_id + session_path to Frontend
    ↓
Doctor records audio & stops
    ↓
Frontend: POST /consultation/session/{session_id}/transcribe
    ↓ (Backend)
Proxy to AI Engine: POST /asr/transcribe
    ↓ (AI Engine - Whisper)
Return diarized transcript + segments
    ↓ (Backend)
Store transcript in ConsultationSession
    ↓
Return to Frontend
    ↓
Display AI-transcribed segments with speaker labels
    ↓
Doctor generates SOAP or ends consultation
```

## New Backend Endpoints

### 1. Start Consultation Session

```
POST /consultation/session/start

Request Body:
{
  "patient_id": "P001",
  "visit_id": "V001",
  "doctor_id": "D001"
}

Response:
{
  "session_id": "abc123-def456",
  "patient_id": "P001",
  "visit_id": "V001",
  "session_path": "P001/V001/abc123-def456",
  "started_at": "2024-05-18T10:30:00Z"
}
```

### 2. Upload & Transcribe Audio

```
POST /consultation/session/{session_id}/transcribe

Content-Type: multipart/form-data
- file: [audio blob]

Response:
{
  "session_id": "abc123-def456",
  "transcript": "Full transcription text...",
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.0,
      "end": 5.2,
      "translation": "Doctor: Hello, how are you feeling today?"
    },
    {
      "speaker": "SPEAKER_01",
      "start": 5.3,
      "end": 8.1,
      "translation": "Patient: I've been having a fever..."
    }
  ],
  "duration_seconds": 120.5,
  "status": "transcribed"
}
```

### 3. End Consultation Session

```
POST /consultation/session/{session_id}/end

Request Body:
{
  "transcript": "Full transcript...",
  "transcript_segments": [...],
  "duration_seconds": 120.5
}

Response:
{
  "session_id": "abc123-def456",
  "patient_id": "P001",
  "visit_id": "V001",
  "status": "completed",
  "ended_at": "2024-05-18T10:32:00Z"
}
```

### 4. Get Session Details

```
GET /consultation/session/{session_id}

Response:
{
  "session_id": "abc123-def456",
  "patient_id": "P001",
  "visit_id": "V001",
  "doctor_id": "D001",
  "started_at": "2024-05-18T10:30:00Z",
  "ended_at": null,
  "duration_seconds": 0,
  "transcript_raw": null,
  "transcript_segments": [],
  "status": "active"
}
```

## Frontend Components

### RecordingSession.jsx Flow

1. **Initialization**
   - Component mounts
   - Calls `POST /consultation/session/start`
   - Sets sessionId and sessionPath
   - Displays session info to doctor

2. **Recording**
   - Doctor clicks "Start Recording"
   - Browser MediaRecorder captures audio
   - WebSpeech API shows live transcript (if supported)
   - Recording timer counts up

3. **Transcription**
   - Doctor clicks "Stop Recording"
   - Audio blob sent to `POST /consultation/session/{session_id}/transcribe`
   - Backend proxies to AI Engine Whisper
   - AI returns speaker-diarized segments
   - Frontend displays segments with speaker labels

4. **Completion**
   - Doctor can:
     - Generate SOAP (navigate to SOAP page)
     - End consultation (saves session + completes visit)
   - Session data persisted on backend

## Data Flow

### Session Path Structure

```
Format: {patient_id}/{visit_id}/{session_id}

Example: P001/V001/550e8400-e29b-41d4-a716-446655440000

Where:
- P001 = Patient ID
- V001 = Visit ID
- 550e8400... = Unique session UUID
```

### Transcript Segments

```javascript
{
  id: "ai-0",
  text: "Hello, how are you feeling?",
  speaker: "SPEAKER_00",  // From Whisper diarization
  start: 0.0,
  end: 3.5,
  confidence: 0.98,      // AI confidence score
  source: "ai-whisper"   // Source identifier
}
```

## Integration Checklist

- [x] Backend: ConsultationSession schema
- [x] Backend: SessionStore (in-memory persistence)
- [x] Backend: Consultation routes
- [x] Backend: Main.py router registration
- [x] Frontend: RecordingSession refactoring
- [x] Frontend: Session initialization
- [x] Frontend: Audio transcription upload
- [x] Frontend: Display AI segments with speakers
- [ ] Backend: Database persistence (optional enhancement)
- [ ] Backend: Session cleanup/archival (optional enhancement)
- [ ] Frontend: Session history view (optional enhancement)

## Usage Example

### From Doctor Dashboard

1. Doctor clicks "Start Consultation" for patient
2. Navigated to `/doctors-dashboard/recording-session/{patientId}/{visitId}`
3. RecordingSession auto-initializes session via API
4. Doctor records conversation
5. System transcribes with Whisper + diarization
6. Doctor generates SOAP or ends consultation

## Current Limitations & Future Enhancements

### Current

- Sessions stored in-memory (lost on server restart)
- No session history/archive
- Basic speaker diarization (Whisper default)

### Future Enhancements

1. **Persistence**: Move SessionStore to database
2. **Streaming**: Real-time Whisper transcription during recording
3. **Speaker Identification**: Map speakers to "Doctor" / "Patient" roles
4. **Editing**: Allow doctors to edit/correct transcription
5. **Export**: Save sessions to patient records
6. **Analytics**: Track consultation metrics (duration, accuracy, etc.)

## Error Handling

### Common Errors

**Session Not Found**

```json
{
  "status_code": 404,
  "detail": "Session abc123 not found"
}
```

**AI Engine Unavailable**

```json
{
  "status_code": 503,
  "detail": "AI engine transcription failed: Connection timeout"
}
```

**Microphone Permission Denied**

```
Error: Unable to access microphone. Please allow mic permission and try again.
```

## Testing

### Test Session Creation

```bash
curl -X POST http://localhost:8000/consultation/session/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <doctor_token>" \
  -d '{
    "patient_id": "P001",
    "visit_id": "V001",
    "doctor_id": "D001"
  }'
```

### Test Transcription

```bash
curl -X POST http://localhost:8000/consultation/session/abc123/transcribe \
  -H "Authorization: Bearer <doctor_token>" \
  -F "file=@recording.webm"
```

## Security Notes

- Session endpoints require authentication (doctor role)
- Session isolation per patient/visit
- Audio not stored on disk (streamed through transcription)
- Session tokens expire after consultation end

## Files Modified

1. **Backend**
   - `app/schemas/consultation.py` (new)
   - `app/repositories/session_store.py` (new)
   - `app/api/routes/consultation.py` (new)
   - `app/main.py` (updated imports & routers)

2. **Frontend**
   - `src/pages/Doctor/RecordingSession.jsx` (refactored)

## Deployment Notes

1. Ensure AI Engine is running and accessible at configured URL
2. Backend and AI Engine must have CORS configured for cross-origin requests
3. WebM audio codec support required in browsers
4. Session memory will reset on backend restart (upgrade to database-backed in production)
