# CLINIQ-FLOW Frontend

The CLINIQ-FLOW frontend is the role-based web workspace for a full inpatient and outpatient electronic medical record system. It is designed for public-hospital workflows where clinicians need clear, fast access to patient information without relying on continuous internet access for clinical transcription.

## Supported workspaces

| Role | Core workflow |
| --- | --- |
| Administrator | Staff account management, hospital catalogue, payment oversight, clinical templates and operational metrics |
| Record officer | Patient registration, search and record maintenance |
| Nurse | Triage queue, vitals capture, urgency review and inpatient nursing observations |
| Doctor | Consultation queue, clinical forms, admissions, discharge summaries, transcript-to-SOAP review and medication safety support |
| Pharmacist | Medication worklist and dispensing workflow |
| Billing officer | Invoices, payment confirmation and billing workspace |

The hospital catalogue supports outpatient clinics and inpatient locations including wards, emergency units, theatre, ICU and antenatal care. Administrators can extend the catalogue for a hospital without a frontend release.

## Clinical decision support

- Voice recordings are sent to the backend, which calls the protected offline AI engine. The browser never receives the AI service token.
- The ASR service uses the approved Yoruba Whisper small model and supports Yoruba, English and mixed speech. It creates an editable transcript, not a final clinical record.
- SOAP drafts, triage signals and paediatric dose checks are decision support only. They do not diagnose, prescribe or replace clinician judgement.
- Dose checks consider available patient age, weight, dose, frequency and route, show source evidence, and flag values needing review.

## Architecture and security boundary

The application uses Supabase only for browser authentication. Clinical, billing and administrative data flows through the FastAPI backend. The frontend uses the Supabase public URL and anonymous key plus the backend public API URL; these are build-time configuration values, not secrets.

Do not place database URLs, service-role keys, JWT secrets or AI service tokens in `VITE_*` variables.

## Environment variables

Create `.env.local` from `.env.example` and set:

```dotenv
VITE_API_URL=https://api.cliniq-flow.com
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLIC_ANON_KEY
```

For local development, `VITE_API_URL` normally points to `http://localhost:8000`.

## Development

```powershell
pnpm install
pnpm dev
```

Create a production build with:

```powershell
pnpm run build
```

## Deployment

The Vite application is deployed to Vercel. `VITE_API_URL`, `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` must be set as production configuration values in Vercel, followed by a new build. The production API is deployed separately; see the root [README](../README.md) and [deployment readiness guide](../DEPLOYMENT_READINESS.md).

## Clinical rollout requirements

Before patient-data use, validate each role workflow with hospital staff, confirm role access boundaries, test Yoruba/English recordings representative of the intended setting, and obtain clinical governance approval for medication rules, evidence sources and alert thresholds.
