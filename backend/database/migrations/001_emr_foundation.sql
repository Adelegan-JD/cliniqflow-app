-- CLINIQ-FLOW EMR foundation. Apply once to PostgreSQL after the legacy schema.
-- Payments are ledger records only: never store PAN, CVV, bank credentials, or card tokens here.

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    specialty TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clinical_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    code VARCHAR(32) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    location_type TEXT NOT NULL CHECK (location_type IN (
        'outpatient_clinic', 'emergency_unit', 'ward', 'theatre', 'laboratory', 'pharmacy'
    )),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS beds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES clinical_locations(id) ON DELETE RESTRICT,
    code VARCHAR(32) NOT NULL,
    bed_class TEXT NOT NULL DEFAULT 'standard',
    status TEXT NOT NULL DEFAULT 'available' CHECK (status IN (
        'available', 'occupied', 'reserved', 'blocked', 'maintenance'
    )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (location_id, code)
);

-- Extend legacy encounters with a durable care-setting and destination.
ALTER TABLE visitations ADD COLUMN IF NOT EXISTS care_setting TEXT;
ALTER TABLE visitations ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL;
ALTER TABLE visitations ADD COLUMN IF NOT EXISTS location_id UUID REFERENCES clinical_locations(id) ON DELETE SET NULL;
UPDATE visitations
SET care_setting = CASE WHEN visit_type = 'inpatient' THEN 'inpatient' ELSE 'outpatient' END
WHERE care_setting IS NULL;
ALTER TABLE visitations ALTER COLUMN care_setting SET DEFAULT 'outpatient';

CREATE TABLE IF NOT EXISTS admissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admission_number VARCHAR(48) UNIQUE NOT NULL,
    patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE RESTRICT,
    source_visit_id UUID REFERENCES visitations(id) ON DELETE SET NULL,
    admitting_department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    attending_doctor_id VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    admission_type TEXT NOT NULL CHECK (admission_type IN ('emergency', 'elective', 'transfer')),
    status TEXT NOT NULL DEFAULT 'admitted' CHECK (status IN (
        'pending', 'admitted', 'transferred', 'discharged', 'cancelled'
    )),
    admission_reason TEXT NOT NULL,
    admitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    discharged_at TIMESTAMPTZ,
    discharge_disposition TEXT,
    created_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (discharged_at IS NULL OR discharged_at >= admitted_at)
);

CREATE TABLE IF NOT EXISTS bed_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admission_id UUID NOT NULL REFERENCES admissions(id) ON DELETE CASCADE,
    bed_id UUID NOT NULL REFERENCES beds(id) ON DELETE RESTRICT,
    assigned_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_at TIMESTAMPTZ,
    release_reason TEXT,
    CHECK (released_at IS NULL OR released_at >= assigned_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS one_active_bed_assignment_per_bed
ON bed_assignments (bed_id) WHERE released_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS one_active_bed_assignment_per_admission
ON bed_assignments (admission_id) WHERE released_at IS NULL;

CREATE TABLE IF NOT EXISTS billing_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE RESTRICT,
    payer_type TEXT NOT NULL CHECK (payer_type IN ('self_pay', 'nhia', 'private_insurer', 'corporate', 'government')),
    payer_name TEXT,
    member_number TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(48) UNIQUE NOT NULL,
    patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE RESTRICT,
    visit_id UUID REFERENCES visitations(id) ON DELETE SET NULL,
    admission_id UUID REFERENCES admissions(id) ON DELETE SET NULL,
    billing_account_id UUID REFERENCES billing_accounts(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'issued', 'part_paid', 'paid', 'void', 'written_off')),
    currency CHAR(3) NOT NULL DEFAULT 'NGN',
    subtotal_kobo BIGINT NOT NULL DEFAULT 0 CHECK (subtotal_kobo >= 0),
    discount_kobo BIGINT NOT NULL DEFAULT 0 CHECK (discount_kobo >= 0),
    total_kobo BIGINT NOT NULL DEFAULT 0 CHECK (total_kobo >= 0),
    due_at TIMESTAMPTZ,
    issued_at TIMESTAMPTZ,
    created_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    service_code VARCHAR(64),
    description TEXT NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price_kobo BIGINT NOT NULL CHECK (unit_price_kobo >= 0),
    amount_kobo BIGINT NOT NULL CHECK (amount_kobo >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_number VARCHAR(48) UNIQUE NOT NULL,
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
    amount_kobo BIGINT NOT NULL CHECK (amount_kobo > 0),
    currency CHAR(3) NOT NULL DEFAULT 'NGN',
    method TEXT NOT NULL CHECK (method IN ('cash', 'bank_transfer', 'pos', 'online', 'insurance_claim')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'failed', 'reversed', 'refunded')),
    provider_name TEXT,
    provider_reference TEXT UNIQUE,
    received_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    received_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_staff_id VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    actor_role TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    patient_id VARCHAR REFERENCES patients(pid) ON DELETE SET NULL,
    request_id UUID,
    source_ip INET,
    user_agent TEXT,
    before_state JSONB,
    after_state JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_admissions_patient_status ON admissions (patient_id, status, admitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_patient_status ON invoices (patient_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_invoice_status ON payments (invoice_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_entity ON audit_events (entity_type, entity_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_patient ON audit_events (patient_id, occurred_at DESC);
