-- Medication evidence and dose-safety governance.
-- This migration makes each decision reproducible without storing raw audio,
-- payment data, or credentials in the clinical database.

ALTER TABLE medical_knowledge
    ADD COLUMN IF NOT EXISTS source_version TEXT,
    ADD COLUMN IF NOT EXISTS source_sha256 CHAR(64),
    ADD COLUMN IF NOT EXISTS effective_from DATE,
    ADD COLUMN IF NOT EXISTS effective_to DATE,
    ADD COLUMN IF NOT EXISTS approval_status TEXT NOT NULL DEFAULT 'draft',
    ADD COLUMN IF NOT EXISTS approved_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS retired_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS review_due_at DATE;

ALTER TABLE medical_knowledge
    DROP CONSTRAINT IF EXISTS medical_knowledge_approval_status_check;
ALTER TABLE medical_knowledge
    ADD CONSTRAINT medical_knowledge_approval_status_check CHECK (
        approval_status IN ('draft', 'in_review', 'approved', 'retired')
    );
ALTER TABLE medical_knowledge
    DROP CONSTRAINT IF EXISTS medical_knowledge_effective_period_check;
ALTER TABLE medical_knowledge
    ADD CONSTRAINT medical_knowledge_effective_period_check CHECK (
        effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from
    );
ALTER TABLE medical_knowledge
    DROP CONSTRAINT IF EXISTS medical_knowledge_approval_audit_check;
ALTER TABLE medical_knowledge
    ADD CONSTRAINT medical_knowledge_approval_audit_check CHECK (
        approval_status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)
    );

CREATE INDEX IF NOT EXISTS idx_medical_knowledge_governance
ON medical_knowledge (approval_status, is_active, effective_from, effective_to);

CREATE TABLE IF NOT EXISTS dosage_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE RESTRICT,
    visit_id UUID REFERENCES visitations(id) ON DELETE SET NULL,
    admission_id UUID REFERENCES admissions(id) ON DELETE SET NULL,
    order_item_id UUID REFERENCES clinical_order_items(id) ON DELETE SET NULL,
    requested_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    drug_name TEXT NOT NULL,
    patient_age_years NUMERIC(6, 3),
    patient_weight_kg NUMERIC(7, 3),
    requested_dose_mg NUMERIC(12, 3),
    frequency_per_day INTEGER,
    route TEXT,
    safety_level TEXT NOT NULL CHECK (safety_level IN (
        'safe', 'caution', 'unsafe', 'insufficient_data', 'unknown_drug'
    )),
    request_payload JSONB NOT NULL,
    assessment_payload JSONB NOT NULL,
    evidence_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    rule_set_version TEXT NOT NULL,
    model_identifier TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (patient_age_years IS NULL OR patient_age_years >= 0),
    CHECK (patient_weight_kg IS NULL OR patient_weight_kg > 0),
    CHECK (frequency_per_day IS NULL OR frequency_per_day > 0),
    CHECK (visit_id IS NOT NULL OR admission_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS dosage_check_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dosage_check_id UUID NOT NULL UNIQUE REFERENCES dosage_checks(id) ON DELETE RESTRICT,
    overridden_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    reason TEXT NOT NULL CHECK (length(trim(reason)) >= 10),
    approved_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK ((approved_by IS NULL AND approved_at IS NULL) OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_dosage_checks_patient_time
ON dosage_checks (patient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dosage_checks_safety_time
ON dosage_checks (safety_level, created_at DESC);

-- Protect evidence and decisions from silent post-hoc alteration. Corrections
-- are separate rows/audit events, preserving what the clinician actually saw.
CREATE OR REPLACE FUNCTION prevent_dosage_check_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'dosage_checks are immutable; create a new check or an override record';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS dosage_checks_immutable ON dosage_checks;
CREATE TRIGGER dosage_checks_immutable
BEFORE UPDATE OR DELETE ON dosage_checks
FOR EACH ROW EXECUTE FUNCTION prevent_dosage_check_mutation();
