-- Dedicated billing role and controlled payment confirmation.
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN (
    'admin', 'doctor', 'nurse', 'record_officer', 'pharmacist', 'lab_scientist', 'billing_officer'
));

CREATE INDEX IF NOT EXISTS idx_payments_provider_reference
ON payments (provider_name, provider_reference) WHERE provider_reference IS NOT NULL;

-- A pending payment cannot exceed the outstanding balance at time of entry.
-- This trigger also protects API-independent imports and administrative SQL.
CREATE OR REPLACE FUNCTION validate_pending_payment_amount()
RETURNS TRIGGER AS $$
DECLARE
    invoice_total BIGINT;
    confirmed_total BIGINT;
    pending_total BIGINT;
BEGIN
    SELECT total_kobo INTO invoice_total FROM invoices WHERE id = NEW.invoice_id FOR UPDATE;
    IF invoice_total IS NULL THEN
        RAISE EXCEPTION 'Invoice does not exist';
    END IF;
    SELECT COALESCE(SUM(amount_kobo), 0) INTO confirmed_total
    FROM payments WHERE invoice_id = NEW.invoice_id AND status = 'confirmed';
    SELECT COALESCE(SUM(amount_kobo), 0) INTO pending_total
    FROM payments WHERE invoice_id = NEW.invoice_id AND status = 'pending'
      AND id <> COALESCE(NEW.id, gen_random_uuid());
    IF NEW.amount_kobo + confirmed_total + pending_total > invoice_total THEN
        RAISE EXCEPTION 'Payment exceeds invoice outstanding balance';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS payments_validate_pending_amount ON payments;
CREATE TRIGGER payments_validate_pending_amount
BEFORE INSERT OR UPDATE OF amount_kobo, status ON payments
FOR EACH ROW EXECUTE FUNCTION validate_pending_payment_amount();
