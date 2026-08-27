# Deployment readiness

CLINIQ-FLOW is deliberately not deployed by this repository. Complete every
item below in staging, record the result, then repeat the applicable checks in
production under an approved change window.

## Before starting containers

- Use a dedicated PostgreSQL database and separate application/migration roles.
  The application role must not own the schema or have permission to alter it.
- Set `DATABASE_URL`, Supabase/JWKS configuration, `AI_ENGINE_TOKEN`, and the
  exact public frontend `CORS_ORIGINS` in secret storage. Do not put secrets in
  Git, Docker images, browser variables, logs, or tickets.
- Keep `CLINIQ_DEV_BYPASS_AUTH=false` and set `APP_ENVIRONMENT=production`.
- Place the approved `LyngualLabs/whisper-small-yoruba` snapshot at
  `models/yoruba-whisper` on the deployment host. It is mounted read-only.
- Place backend and AI `.env` files on the host with restrictive permissions.
- Terminate TLS at a maintained reverse proxy/WAF. Expose only HTTPS 443;
  proxy the frontend at `127.0.0.1:8033` and API at `127.0.0.1:8022`;
  keep the AI engine private to Docker.
- Supply `VITE_API_URL`, `VITE_SUPABASE_URL`, and
  `VITE_SUPABASE_ANON_KEY` as build-time variables. These are public browser
  configuration values, never service-role or database credentials.

## Database release procedure

1. Take an encrypted, restore-tested backup and confirm its retention period.
2. Run the legacy baseline only for a new empty installation:

   ```powershell
   docker compose run --rm --no-deps backend python database/schema.py
   ```

3. Apply reviewed additive migrations exactly once:

   ```powershell
   docker compose run --rm --no-deps backend python -m database.migrate
   ```

4. Confirm every numbered migration and checksum in `schema_migrations`.
5. Run a representative inpatient, outpatient, billing, pharmacy, and
   paediatric-dose-advisory test. Confirm that a dose check and override are
   traceable in the audit records.

Never run the baseline schema creator against an existing production database.
Never edit an applied migration; create the next numbered migration.

## Release gates

- `backend` test suite and `frontend` production build pass.
- `/health/ready` reports ready against PostgreSQL after migration.
- ASR health reports its local model loaded; representative Yoruba and Nigerian
  English recordings are manually reviewed by clinical staff.
- Medication evidence, rules, alert thresholds, and override policy are
  approved, versioned, and review-dated by authorised clinical governance.
- Authentication is tested using real Supabase roles. A user must not be able
  to self-assign any clinical or admin role.
- MFA, least-privilege staff roles, session expiry, audit-retention policy,
  monitoring, alerting, encrypted backups, and a restore drill are approved.
- Run an independent dependency/container vulnerability scan and resolve
  critical/high findings before handling real patient data.
- Build and start the Compose services in staging. Confirm `/healthz` from the
  frontend, `/health/ready` from the backend, and that the AI engine has no
  host-published port. Docker Desktop/the host Docker engine must be running
  before this release gate can be validated.

## Rollback

Application rollback means deploying the prior tested image. Database rollback
is a separate, approved procedure: migrations are additive and clinical audit
data must not be deleted to roll back application code. Restore only from a
verified encrypted backup under the incident/change process.
