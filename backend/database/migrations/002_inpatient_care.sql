-- Inpatient lifecycle records. Apply after 001_emr_foundation.sql.

CREATE TABLE IF NOT EXISTS nursing_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admission_id UUID NOT NULL REFERENCES admissions(id) ON DELETE CASCADE,
    recorded_by VARCHAR NOT NULL REFERENCES users(staff_id) ON DELETE RESTRICT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    temperature_c NUMERIC(4,1) CHECK (temperature_c IS NULL OR temperature_c BETWEEN 25 AND 45),
    pulse_rate INT CHECK (pulse_rate IS NULL OR pulse_rate BETWEEN 0 AND 300),
    respiratory_rate INT CHECK (respiratory_rate IS NULL OR respiratory_rate BETWEEN 0 AND 150),
    systolic_bp INT CHECK (systolic_bp IS NULL OR systolic_bp BETWEEN 0 AND 300),
    diastolic_bp INT CHECK (diastolic_bp IS NULL OR diastolic_bp BETWEEN 0 AND 250),
    oxygen_saturation NUMERIC(5,2) CHECK (oxygen_saturation IS NULL OR oxygen_saturation BETWEEN 0 AND 100),
    pain_score INT CHECK (pain_score IS NULL OR pain_score BETWEEN 0 AND 10),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nursing_observations_admission_time
ON nursing_observations (admission_id, recorded_at DESC);
