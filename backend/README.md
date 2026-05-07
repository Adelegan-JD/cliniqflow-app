# cliniqflow-backend

This folder contains the backend support code for the CliniqFlow application.
It provides database connectivity, user authentication, password hashing, session token generation, and entity registration helpers for staff and patients.

## What’s included

- `auth/jwt.py` - JWT creation, verification, access/refresh token helpers, expiry handling.
- `auth/security.py` - password hashing and authentication helpers, role validation.
- `auth/service.py` - login, refresh, token authorization, and current user lookup.
- `database/config.py` - SQLAlchemy database engine configuration and connection helper.
- `database/schema.py` - data model DDL for tables used by CliniqFlow.
- `database/registration.py` - staff and patient registration workflows.
- `database/id_generator.py` - unique patient and staff ID generation logic.

## Requirements

Dependencies are tracked in `requirements.txt`.

Key packages:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `psycopg2-binary`
- `python-dotenv`
- `pydantic`
- `bcrypt`

## Setup

1. Create a Python virtual environment in the repository root or backend folder.
2. Install backend dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

3. Copy the example environment file:

```powershell
copy backend\.env.example backend\.env
```

4. Update `backend/.env` with your database connection URL and JWT secret values.

## Environment Variables

The backend expects the following environment variables:

- `DATABASE_URL` - PostgreSQL connection URL.
- `JWT_SECRET` - secret used to sign JWT tokens.
- `JWT_ISSUER` - issuer claim for JWTs (default: `cliniqflow-backend`).
- `JWT_AUDIENCE` - audience claim for JWTs (default: `cliniqflow-client`).
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - access token lifetime in minutes.
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - refresh token lifetime in days.
- `BCRYPT_ROUNDS` - bcrypt work factor for password hashing.

## Database Initialization

The backend includes `database/schema.py` for creating the main application tables.
Run it directly after configuring `DATABASE_URL`:

```powershell
python backend\database\schema.py
```

This will create tables for:

- `users`
- `patients`
- `patients_metadata`
- `visitations`
- `triage`
- `queue`
- `consultations`
- `ai_notes`
- `dosage_logs`
- `medical_knowledge`

## Authentication and Session Management

The backend provides JWT-based authentication helpers.

- `auth/security.py` handles password hashing and verification.
- `auth/jwt.py` builds signed JWTs and verifies them.
- `auth/service.py` exposes login, refresh, and role-based authorization flows.

Typical flow:

1. Authenticate staff credentials with `auth/security.authenticate_staff`.
2. Issue tokens using `auth/jwt.create_access_token` and `auth/jwt.create_refresh_token`.
3. Verify bearer tokens from requests using `auth/service.extract_bearer_token` and `auth/service.authorize_staff_token`.

## Registration and ID Generation

- `database/registration.py` handles staff and patient creation.
- `database/id_generator.py` reserves unique IDs for staff and patients.

Staff IDs use role-based prefixes such as `ADM-xxxx`, `DOC-xxxx`, `NUR-xxxx`, and `REC-xxxx`.
Patient IDs use `PID` with a date-based code and random digits.

## Production verification

To verify the live patient-registration flow end-to-end, send a real Supabase JWT in the `Authorization` header and post to the production API.

Example request payload:

```json
{
  "firstName": "Ada",
  "lastName": "Okafor",
  "dob": "1994-05-12",
  "gender": "Female",
  "phone": "08012345678",
  "address": "12 Unity Road, Lagos",
  "nokName": "Chinedu Okafor",
  "nokRelationship": "Brother",
  "nokPhone": "08087654321",
  "email": "ada@example.com",
  "state": null,
  "lga": null,
  "nokAddress": null
}
```

The backend will:

- create a row in `patients`
- create a row in `patients_metadata` when metadata is present
- attach `registered_by` to the authenticated record officer’s `staff_id`

If the request succeeds, the API returns the new `pid` and patient `id`.

## Integration Notes

This folder is designed as the core backend module for CliniqFlow.
A FastAPI application can import these modules to implement actual API endpoints for login, registration, patient lookup, and authorization.

Example import paths:

```python
from database.config import engine
from auth.service import login_staff, get_current_staff, refresh_staff_session
from database.registration import register_staff, register_patient
```

## Testing

There are no dedicated test files in this folder yet.
For local validation, ensure the database connection works and the schema can be created.

## Troubleshooting

- If `DATABASE_URL` is missing, `database/config.py` raises an error on import.
- If `JWT_SECRET` is missing, `auth/jwt.py` will raise a validation error.
- Use `BCRYPT_ROUNDS=12` or higher for production; lower values are acceptable only for local development.

## License

Use this backend code according to your project policies.

# Backend

FastAPI service. Runs on **port 8000** by default.

## Run locally

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`  
**Windows (cmd):** `.\.venv\Scripts\activate.bat`

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- **Docs:** http://127.0.0.1:8000/docs
- **Health:** http://127.0.0.1:8000/health (`persistence` is `postgres` only if `DATABASE_URL` is set)

## Tests

```bash
pytest
```
