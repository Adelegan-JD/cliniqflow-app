from database.config import engine
from sqlalchemy import text


def create_tables():
    ddl_statements = [
        """
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            staff_id VARCHAR UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            other_names TEXT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (
                role IN (
                    'admin',
                    'doctor',
                    'nurse',
                    'record_officer',
                    'pharmacist',
                    'lab_scientist'
                )
            ),
            department TEXT,
            license_number TEXT,
            status TEXT NOT NULL DEFAULT 'Offline' CHECK (
                status IN ('Present', 'Offline', 'On Leave')
            ),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patients (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pid VARCHAR UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            other_names TEXT,
            date_of_birth DATE NOT NULL,
            gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
            age INT CHECK (age IS NULL OR age >= 0),
            passport_url TEXT,
            registered_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patients_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            patient_id VARCHAR UNIQUE NOT NULL REFERENCES patients(pid) ON DELETE CASCADE,
            email TEXT,
            phone TEXT,
            other_phone_number TEXT,
            address TEXT,
            state_of_origin TEXT,
            lga TEXT,
            nationality TEXT,
            tribe TEXT,
            religion TEXT,
            education TEXT,
            civil_status TEXT CHECK (
                civil_status IN ('Single', 'Married', 'Divorced', 'Widowed', 'Separated')
            ),
            nin TEXT,
            nhis_number TEXT,
            military_service_number TEXT,
            next_of_kin_name TEXT,
            next_of_kin_relationship TEXT,
            next_of_kin_phone TEXT,
            next_of_kin_address TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS visitations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            visit_number VARCHAR UNIQUE NOT NULL,
            patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE CASCADE,
            checked_in_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
            visit_type TEXT NOT NULL DEFAULT 'walk_in' CHECK (
                visit_type IN ('walk_in', 'appointment', 'follow_up', 'emergency', 'inpatient')
            ),
            reason_for_visit TEXT,
            status TEXT NOT NULL DEFAULT 'active' CHECK (
                status IN ('active', 'completed', 'cancelled')
            ),
            arrival_time TIMESTAMPTZ DEFAULT NOW(),
            departure_time TIMESTAMPTZ,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS triage (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            visit_id UUID REFERENCES visitations(id) ON DELETE CASCADE,
            patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE CASCADE,
            nurse_id VARCHAR NOT NULL REFERENCES users(staff_id),
            chief_complaint TEXT NOT NULL,
            symptoms TEXT,
            temperature_c NUMERIC(4, 1),
            pulse_rate INT CHECK (pulse_rate IS NULL OR pulse_rate >= 0),
            respiratory_rate INT CHECK (respiratory_rate IS NULL OR respiratory_rate >= 0),
            systolic_bp INT CHECK (systolic_bp IS NULL OR systolic_bp >= 0),
            diastolic_bp INT CHECK (diastolic_bp IS NULL OR diastolic_bp >= 0),
            oxygen_saturation NUMERIC(5, 2) CHECK (
                oxygen_saturation IS NULL OR (
                    oxygen_saturation >= 0 AND oxygen_saturation <= 100
                )
            ),
            weight_kg NUMERIC(6, 2) CHECK (weight_kg IS NULL OR weight_kg >= 0),
            height_cm NUMERIC(6, 2) CHECK (height_cm IS NULL OR height_cm >= 0),
            allergies TEXT,
            current_medication TEXT,
            medical_history TEXT,
            pain_score INT CHECK (pain_score IS NULL OR pain_score BETWEEN 0 AND 10),
            urgency_level TEXT NOT NULL DEFAULT 'moderate' CHECK (
                urgency_level IN ('low', 'moderate', 'high', 'critical')
            ),
            notes TEXT,
            triaged_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS queue (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            visit_id UUID NOT NULL REFERENCES visitations(id) ON DELETE CASCADE,
            patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE CASCADE,
            triage_id UUID REFERENCES triage(id) ON DELETE SET NULL,
            queue_number VARCHAR UNIQUE,
            priority_level TEXT NOT NULL DEFAULT 'moderate' CHECK (
                priority_level IN ('low', 'moderate', 'high', 'critical')
            ),
            current_stage TEXT NOT NULL DEFAULT 'waiting' CHECK (
                current_stage IN (
                    'waiting',
                    'triage',
                    'consultation',
                    'discharged',
                    'cancelled'
                )
            ),
            status TEXT NOT NULL DEFAULT 'queued' CHECK (
                status IN ('queued', 'in_progress', 'completed', 'cancelled')
            ),
            assigned_staff_id VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
            queued_at TIMESTAMPTZ DEFAULT NOW(),
            called_at TIMESTAMPTZ,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            notes TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS consultations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            visit_id UUID NOT NULL REFERENCES visitations(id) ON DELETE CASCADE,
            patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE CASCADE,
            queue_id UUID REFERENCES queue(id) ON DELETE SET NULL,
            triage_id UUID REFERENCES triage(id) ON DELETE SET NULL,
            doctor_id VARCHAR NOT NULL REFERENCES users(staff_id),
            consultation_type TEXT NOT NULL DEFAULT 'outpatient' CHECK (
                consultation_type IN ('outpatient', 'follow_up', 'emergency', 'inpatient')
            ),
            symptoms TEXT,
            diagnosis TEXT,
            treatment_plan TEXT,
            prescriptions TEXT,
            investigations_ordered TEXT,
            doctor_notes TEXT,
            transcript TEXT,
            follow_up_date DATE,
            status TEXT NOT NULL DEFAULT 'open' CHECK (
                status IN ('open', 'completed', 'referred', 'cancelled')
            ),
            started_at TIMESTAMPTZ DEFAULT NOW(),
            ended_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            visit_id UUID REFERENCES visitations(id) ON DELETE CASCADE,
            patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE CASCADE,
            consultation_id UUID REFERENCES consultations(id) ON DELETE CASCADE,
            triage_id UUID REFERENCES triage(id) ON DELETE SET NULL,
            created_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
            model_name TEXT,
            note_type TEXT NOT NULL DEFAULT 'summary' CHECK (
                note_type IN (
                    'summary',
                    'soap',
                    'triage_assist',
                    'discharge',
                    'clinical_note',
                    'other'
                )
            ),
            prompt TEXT,
            output TEXT NOT NULL,
            source_context JSONB DEFAULT '{}'::jsonb,
            status TEXT NOT NULL DEFAULT 'draft' CHECK (
                status IN ('draft', 'final', 'archived')
            ),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dosage_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            visit_id UUID REFERENCES visitations(id) ON DELETE CASCADE,
            patient_id VARCHAR NOT NULL REFERENCES patients(pid) ON DELETE CASCADE,
            consultation_id UUID REFERENCES consultations(id) ON DELETE SET NULL,
            requested_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
            medication_name TEXT,
            indication TEXT,
            patient_age INT CHECK (patient_age IS NULL OR patient_age >= 0),
            patient_weight_kg NUMERIC(6, 2) CHECK (
                patient_weight_kg IS NULL OR patient_weight_kg >= 0
            ),
            dosage_question TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            ai_model TEXT,
            confidence_score NUMERIC(5, 2) CHECK (
                confidence_score IS NULL OR (
                    confidence_score >= 0 AND confidence_score <= 1
                )
            ),
            audit_status TEXT NOT NULL DEFAULT 'pending_review' CHECK (
                audit_status IN ('pending_review', 'accepted', 'flagged', 'rejected')
            ),
            reviewed_by VARCHAR REFERENCES users(staff_id) ON DELETE SET NULL,
            review_notes TEXT,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS medical_knowledge (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_key TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            source_name TEXT,
            source_reference TEXT,
            chunk_index INT NOT NULL DEFAULT 0 CHECK (chunk_index >= 0),
            content TEXT NOT NULL,
            tags TEXT[] DEFAULT ARRAY[]::TEXT[],
            metadata_json JSONB DEFAULT '{}'::jsonb,
            embedding_status TEXT NOT NULL DEFAULT 'pending' CHECK (
                embedding_status IN ('pending', 'processed', 'failed')
            ),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (document_key, chunk_index)
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_users_role_status
        ON users (role, status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_patients_name
        ON patients (last_name, first_name);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_visitations_patient_status
        ON visitations (patient_id, status, arrival_time DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_triage_visit_patient
        ON triage (visit_id, patient_id, urgency_level);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_queue_status_priority
        ON queue (status, priority_level, queued_at);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_queue_visit_patient
        ON queue (visit_id, patient_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_consultations_doctor_status
        ON consultations (doctor_id, status, started_at DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_consultations_visit_patient
        ON consultations (visit_id, patient_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ai_notes_lookup
        ON ai_notes (patient_id, consultation_id, note_type, created_at DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_dosage_logs_lookup
        ON dosage_logs (patient_id, consultation_id, audit_status, created_at DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_medical_knowledge_active_category
        ON medical_knowledge (is_active, category);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_medical_knowledge_search
        ON medical_knowledge
        USING GIN (to_tsvector('english', coalesce(title, '') || ' ' || content));
        """,
    ]

    try:
        with engine.begin() as conn:
            for statement in ddl_statements:
                conn.execute(text(statement))
        print("Tables created successfully")
    except Exception as e:
        print("Error creating tables:", str(e))


if __name__ == "__main__":
    create_tables()
