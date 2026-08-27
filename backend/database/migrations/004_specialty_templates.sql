-- Configurable clinical documentation for specialty clinics.
-- Template schemas and responses are validated by the application; records stay immutable by version.

CREATE TABLE IF NOT EXISTS clinical_form_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    schema_json JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1 CHECK (version > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (department_id, code, version)
);

CREATE TABLE IF NOT EXISTS clinical_form_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES clinical_form_templates(id) ON DELETE RESTRICT,
    template_version INT NOT NULL CHECK (template_version > 0),
    patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE RESTRICT,
    visit_id UUID REFERENCES visitations(id) ON DELETE SET NULL,
    admission_id UUID REFERENCES admissions(id) ON DELETE SET NULL,
    recorded_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'final', 'amended')),
    response_json JSONB NOT NULL,
    finalized_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (visit_id IS NOT NULL OR admission_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_clinical_forms_patient ON clinical_form_responses (patient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clinical_forms_visit ON clinical_form_responses (visit_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clinical_forms_admission ON clinical_form_responses (admission_id, created_at DESC);
