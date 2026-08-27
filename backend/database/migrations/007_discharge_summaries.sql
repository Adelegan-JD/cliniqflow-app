-- Signed inpatient discharge summaries. Final records are never overwritten.

CREATE TABLE IF NOT EXISTS discharge_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admission_id UUID UNIQUE NOT NULL REFERENCES admissions(id) ON DELETE RESTRICT,
    patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE RESTRICT,
    authored_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'final')),
    admission_diagnosis TEXT,
    discharge_diagnosis TEXT NOT NULL,
    hospital_course TEXT NOT NULL,
    procedures_performed TEXT,
    discharge_medications TEXT,
    follow_up_instructions TEXT,
    condition_at_discharge TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalized_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_discharge_summaries_patient ON discharge_summaries (patient_id, created_at DESC);
