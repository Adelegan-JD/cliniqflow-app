# CliniqFlow

CliniqFlow is an end-to-end clinical workflow platform that combines a role-based web app, a FastAPI backend, and an AI engine for triage support, clinical note structuring, speech-to-text, and medication guidance. It is designed to streamline patient intake, visits, and documentation across record officers, nurses, doctors, and admins.

CliniqFlow is a decision-support tool. It organizes information and flags issues, but does not diagnose.

## What this project does

- Patient registration and visit creation (record officer workflows)
- Nurse triage capture and urgency assessment
- Doctor queue management and visit documentation (SOAP summaries)
- AI assistance for vitals-based urgency, transcript-to-SOAP structuring, and clinical validations
- ASR (audio transcription with speaker diarization)
- RAG-based medication guidance and dose validation

## Architecture at a glance

flowchart LR
  F[Frontend (React + Vite)] -->|REST + JWT| B[Backend API (FastAPI)]
  B -->|HTTP + Bearer token| A[AI Engine (FastAPI)]
  B -->|SQLAlchemy| DB[(PostgreSQL)]
  A -->|RAG files| KB[(Medication knowledge files)]
  A -->|Models| ASR[Whisper + Pyannote]
```

## Core workflows

1) Registration and visit
- Record officer registers a patient and creates a visit.
- Visit enters the triage queue with status WAITING_FOR_TRIAGE.

2) Nurse triage
- Nurse views the triage queue and submits vitals.
- Backend can call the AI engine to produce urgency level and abnormal-vital reasons.

3) Doctor encounter
- Doctor starts an exam from the queue.
- Doctor saves the visit with SOAP notes, prescriptions, and transcript.
- Backend can request AI-generated SOAP output from transcript.

4) AI assistance
- NLP: vitals urgency and transcript-to-SOAP structuring.
- RAG: medication evidence retrieval and dose validation rules.
- ASR: diarized transcription of uploaded audio files.

## Folder structure

```
.
├── ai_engine/                     # AI engine service (NLP, ASR, RAG)
│   ├── app/
│   │   ├── api/
│   │   │   ├── asr_api.py
│   │   │   └── rag_api.py
│   │   ├── asr/
│   │   ├── nlp/
│   │   │   ├── api/
│   │   │   ├── models/
│   │   │   └── src/
│   │   └── Rag/
│   │       ├── files/
│   │       └── ...
│   ├── main.py
│   └── requirements.txt
├── backend/                       # Core API, auth, data layer, orchestration
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── auth/
│   ├── database/
│   ├── tests/
│   └── requirements.txt
├── frontend/                      # React UI
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── store/
│   │   └── utils/
│   ├── index.html
│   └── package.json
├── context.txt                    # Data tables quick reference
└── PATIENT_DATA_FLOW_ANALYSIS.md  # Detailed flow analysis
```

## Services and responsibilities

### Frontend (React + Vite)
- Location: frontend
- Responsibilities:
  - Role-based UI: admin, record officer, nurse, doctor
  - Registration, triage, queues, records, and dashboards
  - Uses `VITE_API_URL` to reach the backend
  - Uses Supabase client for auth

### Backend API (FastAPI)
- Location: backend
- Responsibilities:
  - Role-based REST endpoints
  - Patient and visit lifecycle
  - Auth and access control (Supabase JWT or dev-bypass)
  - Orchestration to AI engine

### AI Engine (FastAPI)
- Location: ai_engine
- Responsibilities:
  - NLP workflows for triage and SOAP structuring
  - RAG medication retrieval and dose validation
  - ASR transcription with diarization

## Backend API overview

Role-scoped endpoints (backend/app/api/routes):
- /record-officer: patient registration, search, visit creation, dashboards
- /nurse: triage queue, triage submission, nurse stats
- /doctor: doctor queue, exam start/cancel, save visit, doctor stats
- /admin: staff invitation, metrics, admin stats
- /patients and /visits: REST-style resources for integrations
- /ai, /nlp, /translate/chunk: orchestration to AI engine

Docs: http://127.0.0.1:8000/docs

## AI Engine API overview

- /nlp/vitals-urgency: nurse vitals to urgency assessment
- /nlp/nurse-to-doctor: nurse handoff to SOAP + structured data
- /nlp/process: legacy transcript processing
- /rag/retrieve: evidence retrieval from medication knowledge files
- /rag/validate-dose: deterministic dose safety checks
- /asr/transcribe: diarized transcription from audio upload

Docs: http://127.0.0.1:8001/docs

## Data model (core tables)

- patients: core patient identity
- patients_metadata: contact, next of kin, and demographics
- users: staff accounts and roles
- triage: vitals, urgency, nurse assessments
- queue: visit queue state
- consultations: doctor encounter data
- ai_notes: AI-generated outputs
- dosage_logs: medication validation audits
- medical_knowledge: RAG knowledge sources
- visitation: visit history


Note: the AI engine loads Whisper and diarization models. First run may take time and download model files.



## Testing

Backend:
pytest
```

AI engine:
pytest
```


