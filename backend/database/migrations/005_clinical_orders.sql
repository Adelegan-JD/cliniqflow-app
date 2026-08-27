-- Shared orders for outpatient and inpatient care. Execution is handled by the
-- responsible department; medication administration is intentionally separate.

CREATE TABLE IF NOT EXISTS clinical_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(48) UNIQUE NOT NULL,
    patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE RESTRICT,
    visit_id UUID REFERENCES visitations(id) ON DELETE SET NULL,
    admission_id UUID REFERENCES admissions(id) ON DELETE SET NULL,
    order_type TEXT NOT NULL CHECK (order_type IN ('laboratory', 'imaging', 'procedure', 'medication')),
    priority TEXT NOT NULL DEFAULT 'routine' CHECK (priority IN ('routine', 'urgent', 'stat')),
    status TEXT NOT NULL DEFAULT 'requested' CHECK (status IN ('requested', 'accepted', 'in_progress', 'completed', 'cancelled')),
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    ordered_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    ordered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    clinical_indication TEXT,
    notes TEXT,
    cancelled_at TIMESTAMPTZ,
    cancelled_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (visit_id IS NOT NULL OR admission_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS clinical_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES clinical_orders(id) ON DELETE CASCADE,
    item_code VARCHAR(64),
    name TEXT NOT NULL,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'requested' CHECK (status IN ('requested', 'accepted', 'in_progress', 'completed', 'cancelled')),
    result_text TEXT,
    result_json JSONB,
    resulted_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
    resulted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clinical_orders_patient ON clinical_orders (patient_id, ordered_at DESC);
CREATE INDEX IF NOT EXISTS idx_clinical_orders_worklist ON clinical_orders (order_type, status, priority, ordered_at);
CREATE INDEX IF NOT EXISTS idx_clinical_order_items_order ON clinical_order_items (order_id, status);
