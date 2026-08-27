-- Medication dispensing and administration records (MAR).
-- Only medication order items may be dispensed or administered.

CREATE TABLE IF NOT EXISTS medication_dispenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_item_id UUID NOT NULL REFERENCES clinical_order_items(id) ON DELETE RESTRICT,
    dispensed_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    quantity NUMERIC(10,2) NOT NULL CHECK (quantity > 0),
    unit TEXT NOT NULL,
    batch_number TEXT,
    expiry_date DATE,
    status TEXT NOT NULL DEFAULT 'dispensed' CHECK (status IN ('dispensed', 'returned', 'cancelled')),
    dispensed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS medication_administrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_item_id UUID NOT NULL REFERENCES clinical_order_items(id) ON DELETE RESTRICT,
    dispense_id UUID REFERENCES medication_dispenses(id) ON DELETE SET NULL,
    administered_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    scheduled_for TIMESTAMPTZ,
    administered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dose_quantity NUMERIC(10,2),
    dose_unit TEXT,
    route TEXT,
    status TEXT NOT NULL CHECK (status IN ('given', 'held', 'refused', 'missed', 'not_available')),
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK ((status = 'given' AND dose_quantity IS NOT NULL AND dose_quantity > 0 AND dose_unit IS NOT NULL)
        OR (status <> 'given' AND reason IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_medication_dispenses_order_item ON medication_dispenses (order_item_id, dispensed_at DESC);
CREATE INDEX IF NOT EXISTS idx_medication_administrations_order_item ON medication_administrations (order_item_id, administered_at DESC);
