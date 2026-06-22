# CliniqFlow Backend

The backend is the central API and data layer for CliniqFlow. It manages patient records, visits, triage, and staff access, and it orchestrates calls to the AI engine when clinical automation is needed. This is the service that the frontend talks to.

At a glance:
- Exposes role-based REST APIs for record officers, nurses, doctors, and admins
- Persists patient, visit, and triage data in PostgreSQL (or in-memory if not configured)
- Validates access using Supabase JWTs (or a local JWT flow when enabled)
- Proxies AI workflows (SOAP, vitals urgency, transcription) to the AI engine

## What this backend is responsible for

- Identity and access
  - Role-based authorization for admin, doctor, nurse, and record officer
  - Supabase JWT verification with optional local JWT fallback
- Clinical workflow state
  - Patient registration and search
  - Visit creation and queue state
  - Nurse triage submission
  - Doctor encounter documentation and SOAP summaries
- Orchestration to AI engine
  - Vitals urgency scoring
  - Transcript-to-SOAP processing
  - Audio transcription proxying

## Key workflows (plain English)

1) Record officer registers a patient
- Creates a patient profile and optional metadata.

2) Record officer creates a visit
- Visit enters the triage queue with a WAITING_FOR_TRIAGE status.

3) Nurse triage
- Nurse captures vitals and urgency, which can be sent to the AI engine for scoring.

4) Doctor encounter
- Doctor pulls from queue, records SOAP notes, and closes the visit.

5) Admin operations
- Admin invites staff and tracks metrics.

## API overview

Health
- GET /health

Record officer
- GET /record-officer/dashboard
- GET /record-officer/patients
- GET /record-officer/patients/search
- POST /record-officer/register-patient
- POST /record-officer/visits

Nurse
- GET /nurse/queue
- GET /nurse/stats
- GET /nurse/triage-records
- POST /nurse/triage

Doctor
- GET /doctor/queue
- GET /doctor/stats
- GET /doctor/examination-records
- POST /doctor/start-exam
- POST /doctor/cancel-exam
- POST /doctor/save-visit

Admin
- GET /admin/users
- POST /admin/invite-user
- GET /admin/stats
- GET /admin/metrics

REST resources for integrations
- GET /patients
- GET /patients/{patient_id}
- POST /patients
- GET /visits
- GET /visits/{visit_id}
- POST /visits
- POST /visits/{visit_id}/doctor-conversation

AI orchestration
- POST /nlp/vitals-urgency
- POST /ai/guidelines
- POST /ai/dose-check
- POST /translate/chunk

Docs: http://127.0.0.1:8000/docs

## Example requests

Register a patient:

```json
POST /record-officer/register-patient
{
  "firstName": "Ada",
  "lastName": "Okafor",
  "dob": "1994-05-12",
  "gender": "Female",
  "phone": "08012345678",
  "address": "12 Unity Road, Lagos",
  "nokName": "Chinedu Okafor",
  "nokRelationship": "Brother",
  "nokPhone": *******
}
```

Create a visit:

```json
POST /record-officer/visits
{
  "patient_id": "<patient_uuid>",
  "reason_for_visit": "Fever and cough",
  "department": "General Outpatient"
}
```

Submit nurse triage:

```json
POST /nurse/triage
{
  "visit_id": "<visit_id>",
  "patient_id": "<patient_uuid>",
  "urgency_level": "urgent",
  "vitals": {
    "temperature": 38.9,
    "heart_rate": 115,
    "respiratory_rate": 24,
    "oxygen_saturation": 92
  }
}
```


## Authentication and roles

The backend expects a Bearer token. It supports two modes:

- Supabase JWT validation (default)
  - Verifies tokens using Supabase JWT secret or JWKS.
- Local JWT fallback
  - If `JWT_SECRET` is set, the backend can use the local auth helpers in `auth/`.

Dev bypass:
- When `CLINIQ_DEV_BYPASS_AUTH=true`, the backend accepts any Bearer token and uses these debug headers:
  - `X-Debug-Role`
  - `X-Debug-User-Id`
  - `X-Debug-Staff-Id`

Supported roles:
- admin
- doctor
- nurse
- record_officer

## Data and persistence

This service stores clinical workflow data using SQLAlchemy.

Core tables:
- users
- patients
- patients_metadata
- visitations
- triage
- queue
- consultations
- ai_notes
- dosage_logs
- medical_knowledge

If `DATABASE_URL` is not configured, the backend uses an in-memory store for development.

## Environment variables

Core:
- DATABASE_URL: PostgreSQL connection string
- CORS_ORIGINS: comma-separated list of allowed origins

Supabase JWT:
- SUPABASE_URL
- SUPABASE_JWT_SECRET
- SUPABASE_JWT_ISSUER (optional)
- SUPABASE_JWKS_URL (optional)
- SUPABASE_JWT_VERIFY_AUD (true or false)

AI engine orchestration:
- AI_ENGINE_URL :
- AI_ENGINE_TOKEN (Bearer token used for AI engine calls)

Local auth fallback:
- JWT_SECRET (enables local JWT validation helpers)

Dev mode:
- CLINIQ_DEV_BYPASS_AUTH (true or false)

## Folder structure

```
backend/
├── app/
│   ├── api/routes/          # REST endpoints by role
│   ├── core/                # settings, security, error handling
│   ├── repositories/        # database + in-memory storage
│   ├── schemas/             # request/response contracts
│   └── services/            # AI engine HTTP client
├── auth/                    # local JWT auth helpers (optional)
├── database/                # SQLAlchemy engine + schema
├── tests/
├── requirements.txt
└── README.md
```

## Run locally (Windows PowerShell)

```
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Testing

```
pytest
```

## Troubleshooting

- If `DATABASE_URL` is missing, `database/config.py` will raise an error on import.
- If Supabase JWT validation fails, verify `SUPABASE_URL` and `SUPABASE_JWT_SECRET`.
- If AI calls fail, check `AI_ENGINE_URL` and `AI_ENGINE_TOKEN`.
