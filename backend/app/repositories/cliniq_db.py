"""
PostgreSQL-backed store aligned with `database/schema.py`.
Used when `DATABASE_URL` is set (see `app.repositories` package init).
"""

from __future__ import annotations
from datetime import datetime, time, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import secrets
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database.config import engine
from database.registration import register_patient as db_register_patient
from database.registration import register_staff as db_register_staff

from app.core.visit_status import (
    CANCELLED,
    COMPLETED,
    WAITING_FOR_DOCTOR,
    WAITING_FOR_TRIAGE,
    WITH_DOCTOR,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _require_conn():
    if engine is None:
        raise RuntimeError("Database engine is not configured.")


def _normalize_gender(g: str) -> str:
    m = {
        "male": "Male",
        "female": "Female",
        "m": "Male",
        "f": "Female",
        "other": "Other",
    }
    k = (g or "").strip().lower()
    return m.get(k, g if g in ("Male", "Female", "Other") else "Other")


def _normalize_civil(s: str | None) -> str | None:
    if not s:
        return None
    allowed = {
        "single": "Single",
        "married": "Married",
        "divorced": "Divorced",
        "widowed": "Widowed",
        "separated": "Separated",
    }
    return allowed.get(s.strip().lower(), s if s in allowed.values() else "Single")


def _map_frontend_urgency(u: str | None) -> str:
    if not u:
        return "moderate"
    x = u.lower()
    if x == "emergency":
        return "critical"
    if x == "urgent":
        return "high"
    if x == "normal":
        return "low"
    if x in ("low", "moderate", "high", "critical"):
        return x
    return "moderate"


def _map_db_urgency_to_ui(u: str | None) -> str:
    m = {"critical": "emergency", "high": "urgent", "moderate": "normal", "low": "normal"}
    return m.get((u or "moderate").lower(), "normal")


def _visit_number() -> str:
    return f"VST-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"


def _resolve_patient_pid(conn, ref: str) -> tuple[str | None, str | None]:
    """Return (pid, internal_uuid) for patient id or pid string."""
    ref = (ref or "").strip()
    if not ref:
        return None, None
    row = conn.execute(
        text(
            """
            SELECT pid, id::text AS uid
            FROM patients
            WHERE pid = :r OR id::text = :r
            LIMIT 1;
            """
        ),
        {"r": ref},
    ).mappings().first()
    if not row:
        return None, None
    return row["pid"], row["uid"]


def _api_visit_status(
    visitation_status: str | None,
    queue_stage: str | None,
    queue_status: str | None,
) -> str:
    """Map DB visitation + queue rows to canonical API visit_status."""
    vs = (visitation_status or "active").lower()
    if vs == "completed":
        return COMPLETED
    if vs == "cancelled":
        return CANCELLED
    st = (queue_status or "").lower()
    stage = (queue_stage or "waiting").lower()
    if stage in ("waiting", "triage"):
        return WAITING_FOR_TRIAGE
    if stage == "consultation" and st == "in_progress":
        return WITH_DOCTOR
    if stage == "consultation":
        return WAITING_FOR_DOCTOR
    if stage == "discharged":
        return COMPLETED
    if stage == "cancelled":
        return CANCELLED
    return WAITING_FOR_TRIAGE


def _resolve_visit(conn, key: str) -> dict[str, Any] | None:
    row = conn.execute(
        text(
            """
            SELECT v.*, p.first_name, p.last_name, p.age, p.gender
            FROM visitations v
            JOIN patients p ON p.pid = v.patient_id
            WHERE v.visit_number = :k OR v.id::text = :k
            LIMIT 1;
            """
        ),
        {"k": key},
    ).mappings().first()
    return dict(row) if row else None


class DbStore:
    def list_users_admin(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id::text AS id, staff_id, email,
                           trim(concat_ws(' ', first_name, last_name)) AS name,
                           role
                    FROM users
                    ORDER BY created_at DESC;
                    """
                )
            ).mappings().all()
            return [dict(r) for r in rows]

    def add_user_invite(
        self, email: str, display_name: str, role: str, password: str
    ) -> dict[str, Any]:
        _require_conn()
        parts = display_name.strip().split(None, 1)
        fn = parts[0]
        ln = parts[1] if len(parts) > 1 else parts[0]
        rlow = role.strip().lower().replace(" ", "_")
        return db_register_staff(
            email=email,
            password=password,
            first_name=fn,
            last_name=ln,
            role=rlow,
            phone=None,
            department=None,
            license_number=None,
            status="Offline",
        )

    def admin_stats(self) -> dict[str, int]:
        _require_conn()
        today = date.today()
        with engine.connect() as conn:
            total_patients = conn.execute(
                text("SELECT COUNT(*) FROM patients;")
            ).scalar() or 0
            visits_today = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM visitations
                    WHERE arrival_time::date = :d;
                    """
                ),
                {"d": today},
            ).scalar() or 0
            regs_month = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM patients
                    WHERE created_at >= date_trunc('month', CURRENT_DATE);
                    """
                )
            ).scalar() or 0
            doc_q = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM queue
                    WHERE current_stage IN ('waiting', 'triage', 'consultation')
                      AND status IN ('queued', 'in_progress');
                    """
                )
            ).scalar() or 0
        return {
            "totalPatients": int(total_patients),
            "visitsToday": int(visits_today),
            "newRegistrationsThisMonth": int(regs_month),
            "doctorQueue": int(doc_q),
        }

    def register_patient(self, data: dict[str, Any], registered_by: str | None) -> dict[str, Any]:
        _require_conn()
        meta = {
            "email": data.get("email"),
            "phone": data.get("phone"),
            "other_phone_number": data.get("altPhone"),
            "address": data.get("address"),
            "state_of_origin": data.get("state"),
            "lga": data.get("lga"),
            "nationality": data.get("nationality"),
            "tribe": data.get("tribe"),
            "religion": data.get("religion"),
            "education": data.get("education"),
            "civil_status": _normalize_civil(data.get("civilStatus")),
            "nin": data.get("nin"),
            "nhis_number": data.get("nhisNumber"),
            "military_service_number": data.get("militaryNumber"),
            "next_of_kin_name": data.get("nokName"),
            "next_of_kin_relationship": data.get("nokRelationship"),
            "next_of_kin_phone": data.get("nokPhone"),
            "next_of_kin_address": data.get("nokAddress"),
        }
        patient_payload = {
            "first_name": data["firstName"],
            "last_name": data["lastName"],
            "other_names": data.get("otherNames"),
            "date_of_birth": data["dob"],
            "gender": _normalize_gender(data["gender"]),
            "metadata": meta,
            "registered_by": registered_by,
        }
        out = db_register_patient(**patient_payload)
        p = out["patient"]
        return {
            "id": str(p["id"]),
            "pid": p["pid"],
            "firstName": data["firstName"],
            "lastName": data["lastName"],
            "dob": data["dob"],
            "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
        }

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        _require_conn()
        with engine.connect() as conn:
            pid, _ = _resolve_patient_pid(conn, patient_id)
            if not pid:
                return None
            row = conn.execute(
                text(
                    """
                    SELECT p.*, m.email, m.phone, m.address
                    FROM patients p
                    LEFT JOIN patients_metadata m ON m.patient_id = p.pid
                    WHERE p.pid = :pid;
                    """
                ),
                {"pid": pid},
            ).mappings().first()
            if not row:
                return None
            r = dict(row)
            return {
                "id": str(r["id"]),
                "pid": r["pid"],
                "firstName": r["first_name"],
                "lastName": r["last_name"],
                "dob": str(r["date_of_birth"]) if r.get("date_of_birth") else None,
                "gender": r.get("gender"),
                "phone": r.get("phone"),
                "email": r.get("email"),
            }

    def list_patients(self, search: str | None) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            q = (search or "").strip().lower()
            sql = """
                SELECT p.id, p.pid, p.first_name, p.last_name, p.date_of_birth, p.gender, m.phone
                FROM patients p
                LEFT JOIN patients_metadata m ON m.patient_id = p.pid
            """
            params: dict[str, Any] = {}
            if q:
                sql += """
                WHERE lower(p.pid) LIKE :pat OR lower(p.first_name) LIKE :pat
                   OR lower(p.last_name) LIKE :pat OR lower(coalesce(m.phone,'')) LIKE :pat
                """
                params["pat"] = f"%{q}%"
            sql += " ORDER BY p.created_at DESC LIMIT 500;"
            rows = conn.execute(text(sql), params).mappings().all()
            out = []
            for r in rows:
                out.append(
                    {
                        "id": str(r["id"]),
                        "pid": r["pid"],
                        "firstName": r["first_name"],
                        "lastName": r["last_name"],
                        "dob": str(r["date_of_birth"]) if r.get("date_of_birth") else None,
                        "gender": r.get("gender"),
                        "phone": r.get("phone"),
                    }
                )
            return out

    def search_patients(self, q: str, search_by: str) -> list[dict[str, Any]]:
        _require_conn()
        q = q.strip()
        ql = q.lower()
        with engine.connect() as conn:
            if search_by == "pid":
                rows = conn.execute(
                    text(
                        """
                        SELECT p.id, p.pid, p.first_name, p.last_name, p.date_of_birth, p.gender, m.phone
                        FROM patients p
                        LEFT JOIN patients_metadata m ON m.patient_id = p.pid
                        WHERE lower(p.pid) LIKE :pat;
                        """
                    ),
                    {"pat": f"%{ql}%"},
                ).mappings().all()
            elif search_by == "phone":
                rows = conn.execute(
                    text(
                        """
                        SELECT p.id, p.pid, p.first_name, p.last_name, p.date_of_birth, p.gender, m.phone
                        FROM patients p
                        LEFT JOIN patients_metadata m ON m.patient_id = p.pid
                        WHERE lower(coalesce(m.phone,'')) LIKE :pat;
                        """
                    ),
                    {"pat": f"%{ql}%"},
                ).mappings().all()
            else:
                rows = conn.execute(
                    text(
                        """
                        SELECT p.id, p.pid, p.first_name, p.last_name, p.date_of_birth, p.gender, m.phone
                        FROM patients p
                        LEFT JOIN patients_metadata m ON m.patient_id = p.pid
                        WHERE lower(concat(p.first_name,' ',p.last_name)) LIKE :pat
                           OR cast(p.date_of_birth as text) LIKE :pat2;
                        """
                    ),
                    {"pat": f"%{ql}%", "pat2": f"%{q}%"},
                ).mappings().all()
        return [
            {
                "id": str(r["id"]),
                "pid": r["pid"],
                "name": f"{r['first_name']} {r['last_name']}".strip(),
                "phone": r.get("phone"),
                "dob": str(r["date_of_birth"]) if r.get("date_of_birth") else None,
                "gender": r.get("gender"),
            }
            for r in rows
        ]

    def create_visit(
        self,
        patient_id: str,
        reason_for_visit: str | None,
        department: str | None,
        checked_in_by: str | None,
    ) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            pid, _ = _resolve_patient_pid(conn, patient_id)
            if not pid:
                return None
            
            # Check if patient already has an active visit
            active_visit = conn.execute(
                text(
                    """
                    SELECT id FROM visitations 
                    WHERE patient_id = :pid AND status IN ('active', 'waiting', 'ongoing')
                    LIMIT 1;
                    """
                ),
                {"pid": pid},
            ).scalar()
            
            if active_visit:
                return None  # Patient already has an active visit
            
            vn = _visit_number()
            for _ in range(50):
                try:
                    row = conn.execute(
                        text(
                            """
                            INSERT INTO visitations (
                                visit_number, patient_id, checked_in_by, visit_type,
                                reason_for_visit, status, notes
                            )
                            VALUES (
                                :vn, :pid, :by, 'walk_in', :reason, 'active', :notes
                            )
                            RETURNING id, visit_number, patient_id, arrival_time, status;
                            """
                        ),
                        {
                            "vn": vn,
                            "pid": pid,
                            "by": checked_in_by,
                            "reason": reason_for_visit,
                            "notes": department,
                        },
                    ).mappings().one()
                    vid = row["id"]
                    conn.execute(
                        text(
                            """
                            INSERT INTO queue (
                                visit_id, patient_id, priority_level, current_stage, status
                            )
                            VALUES (
                                :vid, :pid, 'moderate', 'waiting', 'queued'
                            );
                            """
                        ),
                        {"vid": vid, "pid": pid},
                    )
                    pname = conn.execute(
                        text(
                            "SELECT first_name, last_name FROM patients WHERE pid = :p;"
                        ),
                        {"p": pid},
                    ).mappings().first()
                    name = f"{pname['first_name']} {pname['last_name']}".strip()
                    at = row["arrival_time"]
                    iso = at.isoformat() if at else ""
                    return {
                        "visit_id": row["visit_number"],
                        "visit_uuid": str(vid),
                        "patient_id": pid,
                        "patient_name": name,
                        "visit_status": "WAITING_FOR_TRIAGE",
                        "triage_status": "PENDING",
                        "created_at": iso,
                    }
                except IntegrityError:
                    vn = _visit_number()
                    continue
        return None

    def list_visits_values(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT v.visit_number AS visit_id, v.patient_id, v.status AS vstat,
                           v.arrival_time, q.current_stage, q.status AS qstat,
                           p.first_name, p.last_name
                    FROM visitations v
                    JOIN patients p ON p.pid = v.patient_id
                    LEFT JOIN queue q ON q.visit_id = v.id
                    ORDER BY v.arrival_time DESC
                    LIMIT 200;
                    """
                )
            ).mappings().all()
            out = []
            for r in rows:
                api_st = _api_visit_status(r["vstat"], r["current_stage"], r["qstat"])
                tri_st = (
                    "COMPLETE"
                    if (r["current_stage"] or "") == "consultation"
                    else "PENDING"
                )
                out.append(
                    {
                        "visit_id": r["visit_id"],
                        "patient_id": r["patient_id"],
                        "visit_status": api_st,
                        "triage_status": tri_st,
                        "created_at": r["arrival_time"].isoformat()
                        if r["arrival_time"]
                        else "",
                        "patient_name": f"{r['first_name']} {r['last_name']}".strip(),
                    }
                )
            return out

    def get_visit(self, visit_key: str) -> dict[str, Any] | None:
        _require_conn()
        with engine.connect() as conn:
            v = _resolve_visit(conn, visit_key)
            if not v:
                return None
            qrow = conn.execute(
                text(
                    """
                    SELECT current_stage, status FROM queue
                    WHERE visit_id = :vid
                    LIMIT 1;
                    """
                ),
                {"vid": v["id"]},
            ).mappings().first()
            q_stage = qrow["current_stage"] if qrow else None
            q_stat = qrow["status"] if qrow else None
            api_st = _api_visit_status(v.get("status"), q_stage, q_stat)
            return {
                "visit_id": v["visit_number"],
                "patient_id": v["patient_id"],
                "visit_status": api_st,
                "triage_status": "COMPLETE" if q_stage == "consultation" else "PENDING",
                "created_at": v["arrival_time"].isoformat()
                if v.get("arrival_time")
                else None,
            }

    def record_dosage_check(
        self, visit_id: str | None, requested_by: str | None, request: dict[str, Any], assessment: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Persist the exact advisory and evidence shown to the doctor."""
        _require_conn()
        if not visit_id or not requested_by:
            return None
        with engine.begin() as conn:
            visit = _resolve_visit(conn, visit_id)
            if not visit:
                return None
            row = conn.execute(text("""
                INSERT INTO dosage_checks (
                    patient_id, visit_id, requested_by, drug_name, patient_age_years,
                    patient_weight_kg, requested_dose_mg, frequency_per_day, route,
                    safety_level, request_payload, assessment_payload, evidence_snapshot,
                    rule_set_version, model_identifier
                ) VALUES (
                    :patient_id, :visit_id, :requested_by, :drug_name, :age_years,
                    :weight_kg, :dose_mg, :frequency, :route, :safety_level,
                    CAST(:request_payload AS JSONB), CAST(:assessment_payload AS JSONB),
                    CAST(:evidence AS JSONB), :rule_set_version, :model_identifier
                ) RETURNING id::text, created_at;
            """), {
                "patient_id": visit["patient_id"], "visit_id": visit["id"],
                "requested_by": requested_by, "drug_name": request["drug"],
                "age_years": request["age_years"], "weight_kg": request["weight_kg"],
                "dose_mg": request["chosen_dose_mg_per_day"] / request["frequency_per_day"],
                "frequency": request["frequency_per_day"], "route": None,
                "safety_level": assessment.get("safety_level", "insufficient_data"),
                "request_payload": json.dumps(request), "assessment_payload": json.dumps(assessment),
                "evidence": json.dumps(assessment.get("evidence", [])),
                "rule_set_version": "configured-rule-registry-v1",
                "model_identifier": "offline-deterministic-dose-validator",
            }).mappings().one()
            conn.execute(text("""
                INSERT INTO audit_events (actor_staff_id, action, entity_type, entity_id, patient_id, metadata)
                VALUES (:actor, 'dosage_check.created', 'dosage_check', :id, :patient_id,
                    jsonb_build_object('visit_id', :visit_id, 'safety_level', :safety_level));
            """), {"actor": requested_by, "id": row["id"], "patient_id": visit["patient_id"],
                   "visit_id": str(visit["id"]), "safety_level": assessment.get("safety_level", "insufficient_data")})
        return {"id": row["id"], "created_at": row["created_at"].isoformat()}

    def list_visits_for_nurse_queue(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            # Combine active queued visits waiting for triage with patients
            # registered today (new registrations) who should also appear
            # in the nurse triage queue.
            rows = conn.execute(
                text(
                    """
                    SELECT v.visit_number, v.patient_id, v.arrival_time, v.status,
                           p.first_name, p.last_name, p.age, p.gender,
                           q.current_stage, q.status AS qstat
                    FROM visitations v
                    JOIN patients p ON p.pid = v.patient_id
                    JOIN queue q ON q.visit_id = v.id
                    WHERE v.status = 'active'
                      AND q.current_stage = 'waiting'
                      AND q.status = 'queued'

                    UNION

                    SELECT NULL AS visit_number, p.pid AS patient_id, p.created_at AS arrival_time, 'active' AS status,
                           p.first_name, p.last_name, p.age, p.gender,
                           'waiting' AS current_stage, 'queued' AS qstat
                    FROM patients p
                    WHERE p.created_at::date = CURRENT_DATE
                      AND NOT EXISTS (
                        SELECT 1 FROM visitations v2
                        WHERE v2.patient_id = p.pid
                          AND v2.arrival_time::date = CURRENT_DATE
                      )

                    ORDER BY arrival_time ASC;
                    """
                )
            ).mappings().all()
            out = []
            for r in rows:
                api_st = _api_visit_status(r["status"], r["current_stage"], r["qstat"]) 
                out.append(
                    {
                        "visit_id": r["visit_number"],
                        "patient_id": r["patient_id"],
                        "patient_name": f"{r['first_name']} {r['last_name']}".strip(),
                        "visit_status": api_st,
                        "triage_status": "PENDING",
                        "status": "awaiting_triage",
                        "created_at": r["arrival_time"].isoformat()
                        if r["arrival_time"]
                        else "",
                        "age": r.get("age"),
                        "gender": r.get("gender"),
                    }
                )
            return out

    def list_visits_for_doctor_queue(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT v.visit_number, v.patient_id, v.arrival_time, v.status,
                           p.first_name, p.last_name, p.age, p.gender,
                           q.current_stage, q.status AS qstat
                    FROM visitations v
                    JOIN patients p ON p.pid = v.patient_id
                    JOIN queue q ON q.visit_id = v.id
                    WHERE v.status = 'active'
                      AND q.current_stage = 'consultation'
                      AND q.status IN ('queued', 'in_progress')
                    ORDER BY v.arrival_time ASC;
                    """
                )
            ).mappings().all()
            out = []
            for r in rows:
                api_st = _api_visit_status(r["status"], r["current_stage"], r["qstat"])
                out.append(
                    {
                        "visit_id": r["visit_number"],
                        "patient_id": r["patient_id"],
                        "patient_name": f"{r['first_name']} {r['last_name']}".strip(),
                        "visit_status": api_st,
                        "triage_status": "COMPLETE",
                        "created_at": r["arrival_time"].isoformat()
                        if r["arrival_time"]
                        else "",
                        "age": r.get("age"),
                        "gender": r.get("gender"),
                    }
                )
            return out

    def list_triaged_patients_for_doctor(self) -> list[dict[str, Any]]:
        """Get all patients who have completed triage today and are ready for consultation."""
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT v.visit_number, v.patient_id, v.arrival_time, v.status,
                           p.first_name, p.last_name, p.age, p.gender,
                           t.id as triage_id, t.urgency_level, t.triaged_at,
                           q.current_stage, q.status AS qstat
                    FROM visitations v
                    JOIN patients p ON p.pid = v.patient_id
                    JOIN triage t ON t.visit_id = v.id
                    JOIN queue q ON q.visit_id = v.id
                    WHERE v.status = 'active'
                      AND q.current_stage = 'consultation'
                      AND t.triaged_at::date = CURRENT_DATE
                    ORDER BY t.triaged_at DESC;
                    """
                )
            ).mappings().all()
            out = []
            for r in rows:
                api_st = _api_visit_status(r["status"], r["current_stage"], r["qstat"])
                ui_urg = _map_db_urgency_to_ui(r["urgency_level"])
                out.append(
                    {
                        "visit_id": r["visit_number"],
                        "patient_id": r["patient_id"],
                        "patient_name": f"{r['first_name']} {r['last_name']}".strip(),
                        "visit_status": api_st,
                        "triage_status": "COMPLETE",
                        "urgency_level": ui_urg,
                        "triaged_at": r["triaged_at"].isoformat()
                        if r.get("triaged_at")
                        else "",
                        "created_at": r["arrival_time"].isoformat()
                        if r["arrival_time"]
                        else "",
                        "age": r.get("age"),
                        "gender": r.get("gender"),
                    }
                )
            return out

    def start_exam(self, visit_key: str) -> dict[str, Any] | None:
        """Queue row: consultation + queued → in_progress (WITH_DOCTOR)."""
        _require_conn()
        with engine.begin() as conn:
            v = _resolve_visit(conn, visit_key)
            if not v:
                return None
            n = conn.execute(
                text(
                    """
                    UPDATE queue SET
                        status = 'in_progress',
                        started_at = NOW(),
                        called_at = COALESCE(called_at, NOW())
                    WHERE visit_id = :vid
                      AND current_stage = 'consultation'
                      AND status = 'queued'
                    RETURNING id;
                    """
                ),
                {"vid": v["id"]},
            ).scalar()
            if not n:
                return None
        return self.get_visit(visit_key)

    def cancel_exam(self, visit_key: str) -> dict[str, Any] | None:
        """Queue row: consultation + in_progress → queued (WAITING_FOR_DOCTOR)."""
        _require_conn()
        with engine.begin() as conn:
            v = _resolve_visit(conn, visit_key)
            if not v:
                return None
            n = conn.execute(
                text(
                    """
                    UPDATE queue SET
                        status = 'queued',
                        started_at = NULL
                    WHERE visit_id = :vid
                      AND current_stage = 'consultation'
                      AND status = 'in_progress'
                    RETURNING id;
                    """
                ),
                {"vid": v["id"]},
            ).scalar()
            if not n:
                return None
        return self.get_visit(visit_key)

    def end_consultation(self, visit_key: str) -> dict[str, Any] | None:
        """End consultation: mark visit as completed and queue as discharged."""
        _require_conn()
        with engine.begin() as conn:
            v = _resolve_visit(conn, visit_key)
            if not v:
                return None
            
            # Update visitation status to completed
            conn.execute(
                text(
                    """
                    UPDATE visitations SET
                        status = 'completed',
                        departure_time = NOW(),
                        updated_at = NOW()
                    WHERE id = :vid;
                    """
                ),
                {"vid": v["id"]},
            )
            
            # Update queue to completed and discharged
            qrow = conn.execute(
                text(
                    """
                    UPDATE queue SET
                        status = 'completed',
                        current_stage = 'discharged',
                        completed_at = NOW()
                    WHERE visit_id = :vid
                    RETURNING id;
                    """
                ),
                {"vid": v["id"]},
            ).scalar()
            
            if not qrow:
                return None
        
        return self.get_visit(visit_key)

    def doctor_dashboard_stats(self) -> dict[str, int]:
        _require_conn()
        today = date.today()
        with engine.connect() as conn:
            tp = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM visitations WHERE arrival_time::date = :d;
                    """
                ),
                {"d": today},
            ).scalar() or 0
            at = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM queue
                    WHERE current_stage IN ('waiting','triage') AND status != 'completed';
                    """
                )
            ).scalar() or 0
            ac = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM queue
                    WHERE current_stage = 'consultation' AND status = 'in_progress';
                    """
                )
            ).scalar() or 0
            ve = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM visitations
                    WHERE status = 'completed' AND departure_time::date = :d;
                    """
                ),
                {"d": today},
            ).scalar() or 0
        return {
            "totalPatientsToday": int(tp),
            "awaitingTriage": int(at),
            "awaitingConsultation": int(ac),
            "visitsEnded": int(ve),
        }

    def save_triage(
        self,
        visit_id: str,
        patient_id: str,
        vitals: dict[str, Any],
        urgency: str | None,
        nurse_staff_id: str | None,
    ) -> dict[str, Any] | None:
        _require_conn()
        if not nurse_staff_id:
            raise ValueError(
                "staff_id is required to save triage (internal JWT user or dev bypass with staff id)."
            )
        with engine.begin() as conn:
            v = _resolve_visit(conn, visit_id)
            if not v or v["patient_id"] != patient_id:
                pid2, _ = _resolve_patient_pid(conn, patient_id)
                if not v or pid2 != v["patient_id"]:
                    return None
            vid = v["id"]
            chief = vitals.get("chief_complaint") or "Not specified"
            urg = _map_frontend_urgency(urgency)
            tr = conn.execute(
                text(
                    """
                    INSERT INTO triage (
                        visit_id, patient_id, nurse_id, chief_complaint,
                        temperature_c, pulse_rate, respiratory_rate,
                        systolic_bp, diastolic_bp, oxygen_saturation,
                        weight_kg, height_cm, urgency_level
                    )
                    VALUES (
                        :vid, :pid, :nurse, :chief,
                        :temp, :pulse, :rr, :sys, :dia, :spo2, :wk, :ht, :urg
                    )
                    RETURNING id, triaged_at;
                    """
                ),
                {
                    "vid": vid,
                    "pid": v["patient_id"],
                    "nurse": nurse_staff_id,
                    "chief": chief,
                    "temp": float(vitals["temperature"])
                    if vitals.get("temperature") not in (None, "")
                    else None,
                    "pulse": int(vitals["heartRate"])
                    if vitals.get("heartRate") not in (None, "")
                    else None,
                    "rr": int(vitals["respiratoryRate"])
                    if vitals.get("respiratoryRate") not in (None, "")
                    else None,
                    "sys": int(vitals["bpSystolic"])
                    if vitals.get("bpSystolic") not in (None, "")
                    else None,
                    "dia": int(vitals["bpDiastolic"])
                    if vitals.get("bpDiastolic") not in (None, "")
                    else None,
                    "spo2": float(vitals["oxygenSaturation"])
                    if vitals.get("oxygenSaturation") not in (None, "")
                    else None,
                    "wk": float(vitals["weight"])
                    if vitals.get("weight") not in (None, "")
                    else None,
                    "ht": float(vitals["height"])
                    if vitals.get("height") not in (None, "")
                    else None,
                    "urg": urg,
                },
            ).mappings().one()
            tid = tr["id"]
            conn.execute(
                text(
                    """
                    UPDATE queue SET
                        triage_id = :tid,
                        priority_level = :urg,
                        current_stage = 'consultation',
                        status = 'queued'
                    WHERE visit_id = :vid;
                    """
                ),
                {"tid": tid, "urg": urg, "vid": vid},
            )
            pname = conn.execute(
                text(
                    "SELECT first_name, last_name, age, gender FROM patients WHERE pid = :p;"
                ),
                {"p": v["patient_id"]},
            ).mappings().one()
            ui_urg = _map_db_urgency_to_ui(urg)
            return {
                "id": str(tid),
                "visit_id": v["visit_number"],
                "patient_id": v["patient_id"],
                "pid": v["patient_id"],
                "name": f"{pname['first_name']} {pname['last_name']}".strip(),
                "age": pname.get("age"),
                "gender": pname.get("gender"),
                "vitals": vitals,
                "urgencyLevel": ui_urg,
                "triagedAt": tr["triaged_at"].strftime("%Y-%m-%d %H:%M")
                if tr.get("triaged_at")
                else "",
                "vitalsSummary": self._vitals_summary(vitals),
            }

    def _vitals_summary(self, vitals: dict[str, Any]) -> str:
        parts = []
        if vitals.get("temperature"):
            parts.append(f"T {vitals['temperature']}°C")
        if vitals.get("bpSystolic") and vitals.get("bpDiastolic"):
            parts.append(f"BP {vitals['bpSystolic']}/{vitals['bpDiastolic']}")
        if vitals.get("respiratoryRate"):
            parts.append(f"RR {vitals['respiratoryRate']}")
        return ", ".join(parts) if parts else "—"

    def list_triage_records(
        self, urgency: str | None, search: str | None
    ) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT t.id, t.patient_id AS pid, t.urgency_level, t.triaged_at,
                           p.first_name, p.last_name, p.age, p.gender,
                           t.temperature_c, t.systolic_bp, t.diastolic_bp,
                           t.respiratory_rate, t.pulse_rate, t.weight_kg, t.height_cm
                    FROM triage t
                    JOIN patients p ON p.pid = t.patient_id
                    ORDER BY t.triaged_at DESC
                    LIMIT 200;
                    """
                )
            ).mappings().all()
            out = []
            for r in rows:
                uilev = _map_db_urgency_to_ui(r["urgency_level"])
                if urgency:
                    uq = urgency.lower()
                    if uq == "emergency" and uilev != "emergency":
                        continue
                    if uq == "urgent" and uilev != "urgent":
                        continue
                    if uq == "normal" and uilev != "normal":
                        continue
                name = f"{r['first_name']} {r['last_name']}".strip()
                if search and search.lower() not in name.lower() and search.lower() not in (
                    r["pid"] or ""
                ).lower():
                    continue
                out.append(
                    {
                        "id": str(r["id"]),
                        "pid": r["pid"],
                        "name": name,
                        "age": r.get("age"),
                        "gender": r.get("gender"),
                        "urgencyLevel": uilev,
                        "triagedAt": r["triaged_at"].strftime("%Y-%m-%d %H:%M")
                        if r.get("triaged_at")
                        else "",
                        "vitals": {
                            "temperature": r.get("temperature_c"),
                            "bpSystolic": r.get("systolic_bp"),
                            "bpDiastolic": r.get("diastolic_bp"),
                            "respiratoryRate": r.get("respiratory_rate"),
                            "heartRate": r.get("pulse_rate"),
                            "weight": r.get("weight_kg"),
                            "height": r.get("height_cm"),
                        },
                        "vitalsSummary": self._vitals_summary(
                            {
                                "temperature": r.get("temperature_c"),
                                "bpSystolic": r.get("systolic_bp"),
                                "bpDiastolic": r.get("diastolic_bp"),
                                "respiratoryRate": r.get("respiratory_rate"),
                            }
                        ),
                    }
                )
            return out

    def save_visit_encounter(
        self,
        visit_id: str,
        patient_id: str | None,
        transcript: str,
        soap: dict[str, str],
        prescriptions: list[dict[str, Any]],
        doctor_notes: str | None,
        doctor_staff_id: str | None,
    ) -> dict[str, Any]:
        _require_conn()
        if not doctor_staff_id:
            raise ValueError(
                "staff_id is required to save a consultation (internal JWT user or dev bypass with staff id)."
            )
        with engine.begin() as conn:
            v = _resolve_visit(conn, visit_id)
            if not v:
                raise ValueError("visit not found")
            pid = patient_id or v["patient_id"]
            qrow = conn.execute(
                text("SELECT id FROM queue WHERE visit_id = :vid LIMIT 1;"),
                {"vid": v["id"]},
            ).mappings().first()
            qid = qrow["id"] if qrow else None
            trow = conn.execute(
                text(
                    "SELECT id FROM triage WHERE visit_id = :vid ORDER BY triaged_at DESC LIMIT 1;"
                ),
                {"vid": v["id"]},
            ).mappings().first()
            tid = trow["id"] if trow else None
            soap_json = json.dumps(soap)
            pres_json = json.dumps(prescriptions)
            cr = conn.execute(
                text(
                    """
                    INSERT INTO consultations (
                        visit_id, patient_id, queue_id, triage_id, doctor_id,
                        transcript, treatment_plan, prescriptions, doctor_notes, status, ended_at
                    )
                    VALUES (
                        :vid, :pid, :qid, :tid, :doc,
                        :tr, :soap, :rx, :notes, 'completed', NOW()
                    )
                    RETURNING id, created_at;
                    """
                ),
                {
                    "vid": v["id"],
                    "pid": pid,
                    "qid": qid,
                    "tid": tid,
                    "doc": doctor_staff_id,
                    "tr": transcript,
                    "soap": soap_json,
                    "rx": pres_json,
                    "notes": doctor_notes,
                },
            ).mappings().one()
            conn.execute(
                text(
                    """
                    UPDATE visitations SET status = 'completed', departure_time = NOW(), updated_at = NOW()
                    WHERE id = :id;
                    """
                ),
                {"id": v["id"]},
            )
            if qid:
                conn.execute(
                    text(
                        """
                        UPDATE queue SET status = 'completed', current_stage = 'discharged', completed_at = NOW()
                        WHERE id = :qid;
                        """
                    ),
                    {"qid": qid},
                )
            p = conn.execute(
                text(
                    "SELECT * FROM patients WHERE pid = :p;"
                ),
                {"p": pid},
            ).mappings().one()
            meta = conn.execute(
                text(
                    "SELECT * FROM patients_metadata WHERE patient_id = :p;"
                ),
                {"p": pid},
            ).mappings().first()
            triage_data = None
            if tid:
                tg = conn.execute(
                    text(
                        "SELECT urgency_level FROM triage WHERE id = :id;"
                    ),
                    {"id": tid},
                ).mappings().first()
                if tg:
                    triage_data = {
                        "vitals": {},
                        "urgency_level": _map_db_urgency_to_ui(tg["urgency_level"]),
                    }
            return {
                "id": str(cr["id"]),
                "visit_id": v["visit_number"],
                "patient_id": pid,
                "patient_name": f"{p['first_name']} {p['last_name']}".strip(),
                "pid": pid,
                "age": p.get("age"),
                "gender": p.get("gender"),
                "date_of_birth": str(p["date_of_birth"]) if p.get("date_of_birth") else None,
                "phone_number": meta.get("phone") if meta else None,
                "created_at": cr["created_at"].isoformat() if cr.get("created_at") else None,
                "transcript_full": transcript,
                "soap_json": {
                    "subjective": soap.get("subjective", ""),
                    "objective": soap.get("objective", ""),
                    "assessment": soap.get("assessment", ""),
                    "plan": soap.get("plan", ""),
                },
                "prescriptions_json": prescriptions,
                "doctor_notes": doctor_notes,
                "triage_data": triage_data,
            }

    def list_examinations(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT c.id, c.visit_id, c.patient_id, c.transcript,
                           c.treatment_plan, c.prescriptions, c.doctor_notes, c.created_at,
                           p.first_name, p.last_name, p.age, p.gender, p.date_of_birth,
                           m.phone
                    FROM consultations c
                    JOIN patients p ON p.pid = c.patient_id
                    LEFT JOIN patients_metadata m ON m.patient_id = p.pid
                    WHERE c.status = 'completed'
                    ORDER BY c.created_at DESC
                    LIMIT 100;
                    """
                )
            ).mappings().all()
            out = []
            for r in rows:
                soap = {}
                try:
                    soap = json.loads(r["treatment_plan"] or "{}")
                except json.JSONDecodeError:
                    pass
                if isinstance(soap, dict) and "subjective" not in soap:
                    soap = {
                        "subjective": soap.get("subjective", ""),
                        "objective": soap.get("objective", ""),
                        "assessment": soap.get("assessment", ""),
                        "plan": soap.get("plan", ""),
                    }
                rx = []
                try:
                    rx = json.loads(r["prescriptions"] or "[]")
                except json.JSONDecodeError:
                    rx = []
                vid = conn.execute(
                    text("SELECT visit_number FROM visitations WHERE id = :id;"),
                    {"id": r["visit_id"]},
                ).scalar()
                out.append(
                    {
                        "id": str(r["id"]),
                        "visit_id": vid,
                        "patient_id": r["patient_id"],
                        "patient_name": f"{r['first_name']} {r['last_name']}".strip(),
                        "pid": r["patient_id"],
                        "age": r.get("age"),
                        "gender": r.get("gender"),
                        "date_of_birth": str(r["date_of_birth"])
                        if r.get("date_of_birth")
                        else None,
                        "phone_number": r.get("phone"),
                        "created_at": r["created_at"].isoformat()
                        if r.get("created_at")
                        else None,
                        "transcript_full": r.get("transcript") or "",
                        "soap_json": soap
                        if "subjective" in str(soap)
                        else {
                            "subjective": "",
                            "objective": "",
                            "assessment": "",
                            "plan": (r.get("treatment_plan") or "")[:2000],
                        },
                        "prescriptions_json": rx if isinstance(rx, list) else [],
                        "doctor_notes": r.get("doctor_notes"),
                        "triage_data": None,
                    }
                )
            return out

    def record_officer_dashboard(self) -> dict[str, Any]:
        _require_conn()
        today = date.today()
        with engine.connect() as conn:
            vt = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM visitations WHERE arrival_time::date = :d;
                    """
                ),
                {"d": today},
            ).scalar() or 0
            wt = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM queue
                    WHERE current_stage IN ('waiting','triage') AND status = 'queued';
                    """
                )
            ).scalar() or 0
            nr = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM patients WHERE created_at::date = :d;
                    """
                ),
                {"d": today},
            ).scalar() or 0
            ct = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM visitations
                    WHERE status = 'completed' AND departure_time::date = :d;
                    """
                ),
                {"d": today},
            ).scalar() or 0
            wv = conn.execute(
                text(
                    """
                    SELECT v.visit_number, v.arrival_time, p.first_name, p.last_name, q.current_stage
                    FROM visitations v
                    JOIN patients p ON p.pid = v.patient_id
                    LEFT JOIN queue q ON q.visit_id = v.id
                    WHERE v.status = 'active' AND (q.current_stage IS NULL OR q.current_stage = 'waiting')
                    ORDER BY v.arrival_time ASC
                    LIMIT 20;
                    """
                )
            ).mappings().all()
            rv = conn.execute(
                text(
                    """
                    SELECT v.visit_number, v.arrival_time, v.status, p.first_name, p.last_name
                    FROM visitations v
                    JOIN patients p ON p.pid = v.patient_id
                    ORDER BY v.arrival_time DESC
                    LIMIT 8;
                    """
                )
            ).mappings().all()
            rr = conn.execute(
                text(
                    """
                    SELECT id, pid, first_name, last_name, created_at
                    FROM patients
                    ORDER BY created_at DESC
                    LIMIT 8;
                    """
                )
            ).mappings().all()
            todays_records = conn.execute(
                text(
                    """
                    SELECT
                        p.id,
                        p.pid,
                        p.first_name,
                        p.last_name,
                        p.other_names,
                        p.gender,
                        p.date_of_birth,
                        p.created_at,
                        p.registered_by,
                        u.first_name AS officer_first_name,
                        u.last_name AS officer_last_name,
                        u.other_names AS officer_other_names,
                        u.staff_id AS officer_staff_id
                    FROM patients p
                    LEFT JOIN users u ON u.staff_id = p.registered_by
                    WHERE p.created_at::date = :d
                    ORDER BY p.created_at DESC;
                    """
                ),
                {"d": today},
            ).mappings().all()
        return {
            "stats": {
                "visitsToday": int(vt),
                "waitingForTriage": int(wt),
                "newRegistrationsToday": int(nr),
                "completedVisitsToday": ct,
            },
            "queue": [
                {
                    "visit_id": w["visit_number"],
                    "patient_name": f"{w['first_name']} {w['last_name']}".strip(),
                    "status": w["current_stage"] or "waiting",
                    "created_at": w["arrival_time"].isoformat()
                    if w.get("arrival_time")
                    else "",
                }
                for w in wv
            ],
            "recentVisits": [
                {
                    "visit_id": x["visit_number"],
                    "patient_name": f"{x['first_name']} {x['last_name']}".strip(),
                    "visit_status": x["status"],
                    "created_at": x["arrival_time"].isoformat()
                    if x.get("arrival_time")
                    else "",
                }
                for x in rv
            ],
            "recentRegistrations": [
                {
                    "id": str(x["id"]),
                    "pid": x["pid"],
                    "name": f"{x['first_name']} {x['last_name']}".strip(),
                    "created_at": x["created_at"].isoformat()
                    if x.get("created_at")
                    else "",
                }
                for x in rr
            ],
            "todayRecords": [
                {
                    "id": str(x["id"]),
                    "pid": x["pid"],
                    "name": f"{x['first_name']} {x['last_name']}".strip(),
                    "otherNames": x.get("other_names"),
                    "gender": x.get("gender"),
                    "dateOfBirth": x["date_of_birth"].isoformat()
                    if x.get("date_of_birth")
                    else None,
                    "date": x["created_at"].date().isoformat()
                    if x.get("created_at")
                    else None,
                    "time": x["created_at"].strftime("%H:%M:%S")
                    if x.get("created_at")
                    else None,
                    "registeredBy": " ".join(
                        part
                        for part in [
                            x.get("officer_first_name"),
                            x.get("officer_other_names"),
                            x.get("officer_last_name"),
                        ]
                        if part
                    ).strip()
                    or x.get("officer_staff_id")
                    or x.get("registered_by")
                    or "—",
                }
                for x in todays_records
            ],
        }
    
    def list_record_officer_records(self, on_date: str | None = None, skip: int = 0, limit: int = 500) -> list[dict[str, Any]]:
        _require_conn()
        # If no date provided, use today's date to preserve current behavior
        if on_date is None:
            on_date = datetime.utcnow().date().isoformat()
        with engine.connect() as conn:
            sql = """
                SELECT
                    p.id,
                    p.pid,
                    p.first_name,
                    p.last_name,
                    p.other_names,
                    p.gender,
                    p.date_of_birth,
                    p.created_at,
                    p.registered_by,
                    u.first_name AS officer_first_name,
                    u.last_name AS officer_last_name,
                    u.other_names AS officer_other_names,
                    u.staff_id AS officer_staff_id
                FROM patients p
                LEFT JOIN users u ON u.staff_id = p.registered_by
                WHERE p.created_at::date = :d
                ORDER BY p.created_at DESC
                LIMIT :limit OFFSET :skip;
            """
            params = {"d": on_date, "limit": int(limit), "skip": int(skip)}
            rows = conn.execute(text(sql), params).mappings().all()

        return [
            {
                "id": str(x["id"]),
                "pid": x["pid"],
                "name": f"{x['first_name']} {x['last_name']}".strip(),
                "otherNames": x.get("other_names"),
                "gender": x.get("gender"),
                "dateOfBirth": x["date_of_birth"].isoformat() if x.get("date_of_birth") else None,
                "date": x["created_at"].date().isoformat() if x.get("created_at") else None,
                "time": x["created_at"].strftime("%H:%M:%S") if x.get("created_at") else None,
                "registeredBy": " ".join(
                    part for part in [
                        x.get("officer_first_name"),
                        x.get("officer_other_names"),
                        x.get("officer_last_name"),
                    ] if part
                ).strip() or x.get("officer_staff_id") or x.get("registered_by") or "—",
            }
            for x in rows
        ]


    def list_departments(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id::text, code, name, specialty, is_active FROM departments ORDER BY name")).mappings().all()
        return [dict(row) for row in rows]

    def create_department(self, data: dict[str, Any]) -> dict[str, Any]:
        _require_conn()
        with engine.begin() as conn:
            row = conn.execute(text("""
                INSERT INTO departments (code, name, specialty)
                VALUES (:code, :name, :specialty)
                RETURNING id::text, code, name, specialty, is_active, created_at;
            """), data).mappings().one()
        return dict(row)

    def load_starter_catalogue(self, departments: list[tuple[str, str, str]], locations: list[tuple[str, str, str, str | None]]) -> dict[str, int]:
        _require_conn()
        added_departments = 0
        added_locations = 0
        with engine.begin() as conn:
            for code, name, specialty in departments:
                result = conn.execute(text("""
                    INSERT INTO departments (code, name, specialty) VALUES (:code, :name, :specialty)
                    ON CONFLICT (code) DO NOTHING RETURNING id;
                """), {"code": code, "name": name, "specialty": specialty})
                added_departments += 1 if result.first() else 0
            department_ids = {row["code"]: str(row["id"]) for row in conn.execute(text("SELECT id, code FROM departments")).mappings()}
            for code, name, location_type, department_code in locations:
                result = conn.execute(text("""
                    INSERT INTO clinical_locations (department_id, code, name, location_type)
                    VALUES (CAST(:department_id AS UUID), :code, :name, :location_type)
                    ON CONFLICT (code) DO NOTHING RETURNING id;
                """), {"department_id": department_ids.get(department_code), "code": code, "name": name, "location_type": location_type})
                added_locations += 1 if result.first() else 0
        return {"departments_added": added_departments, "locations_added": added_locations}

    def list_locations(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT l.id::text, l.code, l.name, l.location_type, l.department_id::text,
                       l.is_active, d.name AS department_name
                FROM clinical_locations l LEFT JOIN departments d ON d.id = l.department_id
                ORDER BY l.name;
            """)).mappings().all()
        return [dict(row) for row in rows]

    def create_location(self, data: dict[str, Any]) -> dict[str, Any]:
        _require_conn()
        with engine.begin() as conn:
            row = conn.execute(text("""
                INSERT INTO clinical_locations (department_id, code, name, location_type)
                VALUES (CAST(:department_id AS UUID), :code, :name, :location_type)
                RETURNING id::text, department_id::text, code, name, location_type, is_active, created_at;
            """), data).mappings().one()
        return dict(row)

    def list_beds(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT b.id::text, b.code, b.bed_class, b.status, b.location_id::text, l.name AS location_name
                FROM beds b JOIN clinical_locations l ON l.id = b.location_id
                ORDER BY l.name, b.code;
            """)).mappings().all()
        return [dict(row) for row in rows]

    def create_bed(self, data: dict[str, Any]) -> dict[str, Any]:
        _require_conn()
        with engine.begin() as conn:
            row = conn.execute(text("""
                INSERT INTO beds (location_id, code, bed_class)
                VALUES (CAST(:location_id AS UUID), :code, :bed_class)
                RETURNING id::text, location_id::text, code, bed_class, status, created_at;
            """), data).mappings().one()
        return dict(row)

    def list_admissions(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT a.id::text, a.admission_number, a.patient_id, a.status, a.admission_type,
                       a.admission_reason, a.admitted_at, a.discharged_at,
                       trim(concat_ws(' ', p.first_name, p.last_name)) AS patient_name,
                       d.name AS department_name
                FROM admissions a JOIN patients p ON p.pid = a.patient_id
                LEFT JOIN departments d ON d.id = a.admitting_department_id
                ORDER BY a.admitted_at DESC;
            """)).mappings().all()
        return [dict(row) for row in rows]

    def create_admission(self, data: dict[str, Any], created_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            patient_pid, _ = _resolve_patient_pid(conn, data["patient_id"])
            if not patient_pid:
                return None
            number = f"ADM-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
            row = conn.execute(text("""
                INSERT INTO admissions (
                    admission_number, patient_id, source_visit_id, admitting_department_id,
                    attending_doctor_id, admission_type, admission_reason, created_by
                ) VALUES (
                    :admission_number, :patient_id, CAST(:source_visit_id AS UUID),
                    CAST(:admitting_department_id AS UUID), :attending_doctor_id,
                    :admission_type, :admission_reason, :created_by
                ) RETURNING id::text, admission_number, patient_id, status, admission_type,
                    admission_reason, admitted_at, created_at;
            """), {**data, "patient_id": patient_pid, "admission_number": number, "created_by": created_by}).mappings().one()
        return dict(row)

    def assign_bed(self, admission_id: str, bed_id: str, assigned_by: str | None, reason: str | None) -> dict[str, Any] | None:
        """Assign or transfer atomically, preventing two active occupants per bed."""
        _require_conn()
        with engine.begin() as conn:
            admission = conn.execute(text("SELECT id FROM admissions WHERE id = CAST(:id AS UUID) AND status = 'admitted' FOR UPDATE"), {"id": admission_id}).first()
            bed = conn.execute(text("SELECT id FROM beds WHERE id = CAST(:id AS UUID) AND status = 'available' FOR UPDATE"), {"id": bed_id}).first()
            if not admission or not bed:
                return None
            current = conn.execute(text("SELECT bed_id FROM bed_assignments WHERE admission_id = CAST(:id AS UUID) AND released_at IS NULL FOR UPDATE"), {"id": admission_id}).mappings().first()
            if current:
                conn.execute(text("""
                    UPDATE bed_assignments SET released_at = NOW(), release_reason = :reason
                    WHERE admission_id = CAST(:admission_id AS UUID) AND released_at IS NULL;
                """), {"admission_id": admission_id, "previous_bed_id": str(current["bed_id"]), "reason": reason or "transfer"})
                conn.execute(text("UPDATE beds SET status = 'available' WHERE id = CAST(:previous_bed_id AS UUID)"), {"previous_bed_id": str(current["bed_id"])})
            row = conn.execute(text("""
                INSERT INTO bed_assignments (admission_id, bed_id, assigned_by)
                VALUES (CAST(:admission_id AS UUID), CAST(:bed_id AS UUID), :assigned_by)
                RETURNING id::text, admission_id::text, bed_id::text, assigned_by, assigned_at;
            """), {"admission_id": admission_id, "bed_id": bed_id, "assigned_by": assigned_by}).mappings().first()
            conn.execute(text("UPDATE beds SET status = 'occupied' WHERE id = CAST(:bed_id AS UUID)"), {"bed_id": bed_id})
        return dict(row) if row else None

    def discharge_admission(self, admission_id: str, disposition: str, discharged_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            row = conn.execute(text("""
                UPDATE admissions
                SET status = 'discharged', discharged_at = NOW(), discharge_disposition = :disposition, updated_at = NOW()
                WHERE id = CAST(:admission_id AS UUID) AND status = 'admitted'
                RETURNING id::text, admission_number, patient_id, status, discharged_at, discharge_disposition;
            """), {"admission_id": admission_id, "disposition": disposition}).mappings().first()
            if not row:
                return None
            active = conn.execute(text("""
                UPDATE bed_assignments SET released_at = NOW(), release_reason = 'discharged'
                WHERE admission_id = CAST(:admission_id AS UUID) AND released_at IS NULL
                RETURNING bed_id::text;
            """), {"admission_id": admission_id}).mappings().all()
            for assignment in active:
                conn.execute(text("UPDATE beds SET status = 'available' WHERE id = CAST(:bed_id AS UUID)"), {"bed_id": assignment["bed_id"]})
            conn.execute(text("""
                INSERT INTO audit_events (actor_staff_id, action, entity_type, entity_id, patient_id, metadata)
                VALUES (:actor, 'admission.discharged', 'admission', :id, :patient_id, jsonb_build_object('disposition', :disposition));
            """), {"actor": discharged_by, "id": admission_id, "patient_id": row["patient_id"], "disposition": disposition})
        return dict(row)

    def list_nursing_observations(self, admission_id: str) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT id::text, admission_id::text, recorded_by, recorded_at, temperature_c, pulse_rate,
                    respiratory_rate, systolic_bp, diastolic_bp, oxygen_saturation, pain_score, notes
                FROM nursing_observations WHERE admission_id = CAST(:admission_id AS UUID)
                ORDER BY recorded_at DESC;
            """), {"admission_id": admission_id}).mappings().all()
        return [dict(row) for row in rows]

    def record_nursing_observation(self, admission_id: str, data: dict[str, Any], recorded_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        if not recorded_by:
            return None
        with engine.begin() as conn:
            active = conn.execute(text("SELECT id, patient_id FROM admissions WHERE id = CAST(:id AS UUID) AND status = 'admitted'"), {"id": admission_id}).mappings().first()
            if not active:
                return None
            row = conn.execute(text("""
                INSERT INTO nursing_observations (
                    admission_id, recorded_by, temperature_c, pulse_rate, respiratory_rate, systolic_bp,
                    diastolic_bp, oxygen_saturation, pain_score, notes
                ) VALUES (
                    CAST(:admission_id AS UUID), :recorded_by, :temperature_c, :pulse_rate, :respiratory_rate,
                    :systolic_bp, :diastolic_bp, :oxygen_saturation, :pain_score, :notes
                ) RETURNING id::text, admission_id::text, recorded_by, recorded_at, temperature_c, pulse_rate,
                    respiratory_rate, systolic_bp, diastolic_bp, oxygen_saturation, pain_score, notes;
            """), {
                "admission_id": admission_id, "recorded_by": recorded_by,
                "temperature_c": data.get("temperature_c"), "pulse_rate": data.get("pulse_rate"),
                "respiratory_rate": data.get("respiratory_rate"), "systolic_bp": data.get("systolic_bp"),
                "diastolic_bp": data.get("diastolic_bp"), "oxygen_saturation": data.get("oxygen_saturation"),
                "pain_score": data.get("pain_score"), "notes": data.get("notes"),
            }).mappings().one()
        return dict(row)

    def list_invoices(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT i.id::text, i.invoice_number, i.patient_id, i.visit_id::text, i.admission_id::text,
                    i.status, i.currency, i.subtotal_kobo, i.discount_kobo, i.total_kobo, i.created_at,
                    trim(concat_ws(' ', p.first_name, p.last_name)) AS patient_name
                FROM invoices i JOIN patients p ON p.pid = i.patient_id ORDER BY i.created_at DESC;
            """)).mappings().all()
        return [dict(row) for row in rows]

    def list_payments(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT p.id::text, p.receipt_number, p.invoice_id::text, p.amount_kobo, p.currency,
                    p.method, p.status, p.provider_name, p.provider_reference, p.received_at, p.created_at,
                    i.invoice_number, i.patient_id,
                    trim(concat_ws(' ', patient.first_name, patient.last_name)) AS patient_name
                FROM payments p JOIN invoices i ON i.id = p.invoice_id
                JOIN patients patient ON patient.pid = i.patient_id
                ORDER BY p.created_at DESC;
            """)).mappings().all()
        return [dict(row) for row in rows]

    def create_invoice(self, data: dict[str, Any], created_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            patient_pid, _ = _resolve_patient_pid(conn, data["patient_id"])
            if not patient_pid:
                return None
            items = []
            subtotal = 0
            for item in data["items"]:
                amount = round(float(item["quantity"]) * int(item["unit_price_kobo"]))
                items.append({**item, "amount_kobo": amount})
                subtotal += amount
            invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
            invoice = conn.execute(text("""
                INSERT INTO invoices (invoice_number, patient_id, visit_id, admission_id, billing_account_id,
                    status, subtotal_kobo, total_kobo, issued_at, created_by)
                VALUES (:invoice_number, :patient_id, CAST(:visit_id AS UUID), CAST(:admission_id AS UUID),
                    CAST(:billing_account_id AS UUID), 'issued', :subtotal, :subtotal, NOW(), :created_by)
                RETURNING id::text, invoice_number, patient_id, visit_id::text, admission_id::text,
                    status, currency, subtotal_kobo, discount_kobo, total_kobo, issued_at, created_at;
            """), {**data, "patient_id": patient_pid, "invoice_number": invoice_number, "subtotal": subtotal, "created_by": created_by}).mappings().one()
            for item in items:
                conn.execute(text("""
                    INSERT INTO invoice_items (invoice_id, service_code, description, quantity, unit_price_kobo, amount_kobo)
                    VALUES (CAST(:invoice_id AS UUID), :service_code, :description, :quantity, :unit_price_kobo, :amount_kobo);
                """), {**item, "invoice_id": invoice["id"]})
            conn.execute(text("""
                INSERT INTO audit_events (actor_staff_id, action, entity_type, entity_id, patient_id, after_state)
                VALUES (:actor, 'invoice.issued', 'invoice', :id, :patient_id, CAST(:state AS JSONB));
            """), {"actor": created_by, "id": invoice["id"], "patient_id": patient_pid, "state": json.dumps({"total_kobo": subtotal, "currency": "NGN"})})
        return {**dict(invoice), "items": items}

    def record_pending_payment(self, data: dict[str, Any], received_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            invoice = conn.execute(text("SELECT id FROM invoices WHERE id = CAST(:id AS UUID) AND status IN ('issued', 'part_paid') FOR UPDATE"), {"id": data["invoice_id"]}).first()
            if not invoice:
                return None
            committed = conn.execute(text("""
                SELECT COALESCE(SUM(amount_kobo), 0) FROM payments
                WHERE invoice_id = CAST(:invoice_id AS UUID) AND status IN ('pending', 'confirmed');
            """), {"invoice_id": data["invoice_id"]}).scalar() or 0
            total = conn.execute(text("SELECT total_kobo FROM invoices WHERE id = CAST(:invoice_id AS UUID)"), {"invoice_id": data["invoice_id"]}).scalar() or 0
            if int(committed) + int(data["amount_kobo"]) > int(total):
                return None
            receipt_number = f"RCT-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
            row = conn.execute(text("""
                INSERT INTO payments (receipt_number, invoice_id, amount_kobo, method, provider_name, provider_reference, received_by)
                VALUES (:receipt_number, CAST(:invoice_id AS UUID), :amount_kobo, :method,
                    :provider_name, :provider_reference, :received_by)
                RETURNING id::text, receipt_number, invoice_id::text, amount_kobo, currency, method,
                    status, provider_name, provider_reference, created_at;
            """), {**data, "receipt_number": receipt_number, "received_by": received_by}).mappings().one()
        return dict(row)

    def confirm_payment(self, payment_id: str, confirmed_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            payment = conn.execute(text("SELECT id, invoice_id, amount_kobo FROM payments WHERE id = CAST(:id AS UUID) AND status = 'pending' FOR UPDATE"), {"id": payment_id}).mappings().first()
            if not payment:
                return None
            invoice = conn.execute(text("SELECT id, patient_id, total_kobo FROM invoices WHERE id = :id FOR UPDATE"), {"id": payment["invoice_id"]}).mappings().one()
            row = conn.execute(text("""
                UPDATE payments SET status = 'confirmed', received_at = NOW(), updated_at = NOW()
                WHERE id = CAST(:id AS UUID)
                RETURNING id::text, receipt_number, invoice_id::text, amount_kobo, currency, method, status, received_at;
            """), {"id": payment_id}).mappings().one()
            confirmed_total = conn.execute(text("SELECT COALESCE(SUM(amount_kobo), 0) FROM payments WHERE invoice_id = :invoice_id AND status = 'confirmed'"), {"invoice_id": payment["invoice_id"]}).scalar() or 0
            invoice_status = 'paid' if int(confirmed_total) >= int(invoice["total_kobo"]) else 'part_paid'
            conn.execute(text("UPDATE invoices SET status = :status, updated_at = NOW() WHERE id = :id"), {"status": invoice_status, "id": payment["invoice_id"]})
            conn.execute(text("""
                INSERT INTO audit_events (actor_staff_id, action, entity_type, entity_id, patient_id, after_state)
                VALUES (:actor, 'payment.confirmed', 'payment', :id, :patient_id, CAST(:state AS JSONB));
            """), {"actor": confirmed_by, "id": payment_id, "patient_id": invoice["patient_id"], "state": json.dumps({"invoice_status": invoice_status, "amount_kobo": payment["amount_kobo"]})})
        return {**dict(row), "invoice_status": invoice_status}

    def list_clinical_form_templates(self) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT t.id::text, t.department_id::text, t.code, t.name, t.description,
                    t.schema_json, t.version, t.is_active, d.name AS department_name
                FROM clinical_form_templates t
                LEFT JOIN departments d ON d.id = t.department_id
                WHERE t.is_active = TRUE
                ORDER BY d.name NULLS FIRST, t.name;
            """)).mappings().all()
        return [dict(row) for row in rows]

    def create_clinical_form_template(self, data: dict[str, Any], created_by: str | None) -> dict[str, Any]:
        _require_conn()
        with engine.begin() as conn:
            row = conn.execute(text("""
                INSERT INTO clinical_form_templates (department_id, code, name, description, schema_json, created_by)
                VALUES (CAST(:department_id AS UUID), :code, :name, :description, CAST(:schema_json AS JSONB), :created_by)
                RETURNING id::text, department_id::text, code, name, description, schema_json, version, is_active, created_at;
            """), {**data, "schema_json": json.dumps(data["schema_json"]), "created_by": created_by}).mappings().one()
        return dict(row)

    def create_clinical_form_response(self, data: dict[str, Any], recorded_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        if not recorded_by:
            return None
        with engine.begin() as conn:
            template = conn.execute(text("""
                SELECT id, version, schema_json FROM clinical_form_templates
                WHERE id = CAST(:id AS UUID) AND is_active = TRUE FOR SHARE;
            """), {"id": data["template_id"]}).mappings().first()
            patient_pid, _ = _resolve_patient_pid(conn, data["patient_id"])
            if not template or not patient_pid:
                return None
            if data.get("visit_id") and not _resolve_visit(conn, data["visit_id"]):
                return None
            if data.get("admission_id") and not conn.execute(text("SELECT id FROM admissions WHERE id = CAST(:id AS UUID)"), {"id": data["admission_id"]}).first():
                return None
            response = conn.execute(text("""
                INSERT INTO clinical_form_responses (
                    template_id, template_version, patient_id, visit_id, admission_id, recorded_by,
                    status, response_json, finalized_at
                ) VALUES (
                    CAST(:template_id AS UUID), :template_version, :patient_id, CAST(:visit_id AS UUID),
                    CAST(:admission_id AS UUID), :recorded_by, :status, CAST(:response_json AS JSONB),
                    CASE WHEN :status = 'final' THEN NOW() ELSE NULL END
                ) RETURNING id::text, template_id::text, template_version, patient_id, visit_id::text,
                    admission_id::text, recorded_by, status, response_json, finalized_at, created_at;
            """), {**data, "patient_id": patient_pid, "template_version": template["version"], "recorded_by": recorded_by, "response_json": json.dumps(data["response_json"])}).mappings().one()
        return dict(response)

    def list_clinical_form_responses(self, patient_id: str) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            patient_pid, _ = _resolve_patient_pid(conn, patient_id)
            if not patient_pid:
                return []
            rows = conn.execute(text("""
                SELECT r.id::text, r.template_id::text, r.template_version, r.patient_id,
                    r.visit_id::text, r.admission_id::text, r.recorded_by, r.status,
                    r.response_json, r.finalized_at, r.created_at, t.code AS template_code, t.name AS template_name
                FROM clinical_form_responses r
                JOIN clinical_form_templates t ON t.id = r.template_id
                WHERE r.patient_id = :patient_id ORDER BY r.created_at DESC;
            """), {"patient_id": patient_pid}).mappings().all()
        return [dict(row) for row in rows]

    def list_clinical_orders(self, patient_id: str) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            patient_pid, _ = _resolve_patient_pid(conn, patient_id)
            if not patient_pid:
                return []
            rows = conn.execute(text("""
                SELECT o.id::text, o.order_number, o.patient_id, o.visit_id::text, o.admission_id::text,
                    o.order_type, o.priority, o.status, o.ordered_by, o.ordered_at, o.clinical_indication, o.notes,
                    COALESCE(jsonb_agg(jsonb_build_object('id', i.id::text, 'name', i.name, 'status', i.status,
                        'result_text', i.result_text) ORDER BY i.created_at) FILTER (WHERE i.id IS NOT NULL), '[]'::jsonb) AS items
                FROM clinical_orders o LEFT JOIN clinical_order_items i ON i.order_id = o.id
                WHERE o.patient_id = :patient_id GROUP BY o.id ORDER BY o.ordered_at DESC;
            """), {"patient_id": patient_pid}).mappings().all()
        return [dict(row) for row in rows]

    def list_order_worklist(self, order_type: str) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT o.id::text, o.order_number, o.patient_id, o.visit_id::text, o.admission_id::text,
                    o.order_type, o.priority, o.status, o.ordered_at,
                    trim(concat_ws(' ', p.first_name, p.last_name)) AS patient_name,
                    COALESCE(jsonb_agg(jsonb_build_object('id', i.id::text, 'name', i.name, 'item_code', i.item_code,
                        'details_json', i.details_json, 'status', i.status) ORDER BY i.created_at)
                        FILTER (WHERE i.id IS NOT NULL), '[]'::jsonb) AS items
                FROM clinical_orders o JOIN patients p ON p.pid = o.patient_id
                LEFT JOIN clinical_order_items i ON i.order_id = o.id
                WHERE o.order_type = :order_type AND o.status NOT IN ('completed', 'cancelled')
                GROUP BY o.id, p.first_name, p.last_name ORDER BY
                    CASE o.priority WHEN 'stat' THEN 1 WHEN 'urgent' THEN 2 ELSE 3 END, o.ordered_at;
            """), {"order_type": order_type}).mappings().all()
        return [dict(row) for row in rows]

    def create_clinical_order(self, data: dict[str, Any], ordered_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        if not ordered_by:
            return None
        with engine.begin() as conn:
            patient_pid, _ = _resolve_patient_pid(conn, data["patient_id"])
            if not patient_pid:
                return None
            if data.get("visit_id") and not _resolve_visit(conn, data["visit_id"]):
                return None
            if data.get("admission_id") and not conn.execute(text("SELECT id FROM admissions WHERE id = CAST(:id AS UUID)"), {"id": data["admission_id"]}).first():
                return None
            number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
            row = conn.execute(text("""
                INSERT INTO clinical_orders (order_number, patient_id, visit_id, admission_id, order_type,
                    priority, department_id, ordered_by, clinical_indication, notes)
                VALUES (:number, :patient_id, CAST(:visit_id AS UUID), CAST(:admission_id AS UUID), :order_type,
                    :priority, CAST(:department_id AS UUID), :ordered_by, :clinical_indication, :notes)
                RETURNING id::text, order_number, patient_id, visit_id::text, admission_id::text, order_type,
                    priority, status, ordered_by, ordered_at, clinical_indication, notes;
            """), {**data, "number": number, "patient_id": patient_pid, "ordered_by": ordered_by}).mappings().one()
            items = []
            for item in data["items"]:
                created = conn.execute(text("""
                    INSERT INTO clinical_order_items (order_id, item_code, name, details_json)
                    VALUES (CAST(:order_id AS UUID), :item_code, :name, CAST(:details_json AS JSONB))
                    RETURNING id::text, item_code, name, details_json, status, created_at;
                """), {**item, "order_id": row["id"], "details_json": json.dumps(item["details_json"])}).mappings().one()
                items.append(dict(created))
            conn.execute(text("""
                INSERT INTO audit_events (actor_staff_id, action, entity_type, entity_id, patient_id, metadata)
                VALUES (:actor, 'order.created', 'clinical_order', :id, :patient_id, jsonb_build_object('order_type', :order_type));
            """), {"actor": ordered_by, "id": row["id"], "patient_id": patient_pid, "order_type": data["order_type"]})
        return {**dict(row), "items": items}

    def update_clinical_order_status(self, order_id: str, data: dict[str, Any], updated_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            row = conn.execute(text("""
                UPDATE clinical_orders SET status = :status, updated_at = NOW(),
                    cancelled_at = CASE WHEN :status = 'cancelled' THEN NOW() ELSE cancelled_at END,
                    cancelled_by = CASE WHEN :status = 'cancelled' THEN :actor ELSE cancelled_by END,
                    cancellation_reason = CASE WHEN :status = 'cancelled' THEN :reason ELSE cancellation_reason END
                WHERE id = CAST(:id AS UUID) AND status NOT IN ('completed', 'cancelled')
                RETURNING id::text, order_number, patient_id, status, cancelled_at, cancellation_reason, updated_at;
            """), {"id": order_id, "status": data["status"], "reason": data.get("cancellation_reason"), "actor": updated_by}).mappings().first()
        return dict(row) if row else None

    def record_order_item_result(self, item_id: str, data: dict[str, Any], resulted_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        with engine.begin() as conn:
            row = conn.execute(text("""
                UPDATE clinical_order_items SET status = 'completed', result_text = :result_text,
                    result_json = CAST(:result_json AS JSONB), resulted_by = :resulted_by, resulted_at = NOW(), updated_at = NOW()
                WHERE id = CAST(:id AS UUID) AND status <> 'cancelled'
                RETURNING id::text, order_id::text, item_code, name, status, result_text, result_json, resulted_by, resulted_at;
            """), {"id": item_id, "result_text": data.get("result_text"), "result_json": json.dumps(data.get("result_json")) if data.get("result_json") is not None else None, "resulted_by": resulted_by}).mappings().first()
            if not row:
                return None
            conn.execute(text("""
                UPDATE clinical_orders SET status = 'completed', updated_at = NOW()
                WHERE id = CAST(:order_id AS UUID)
                  AND NOT EXISTS (SELECT 1 FROM clinical_order_items WHERE order_id = CAST(:order_id AS UUID) AND status NOT IN ('completed', 'cancelled'));
            """), {"order_id": row["order_id"]})
        return dict(row)

    def dispense_medication(self, order_item_id: str, data: dict[str, Any], dispensed_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        if not dispensed_by:
            return None
        with engine.begin() as conn:
            item = conn.execute(text("""
                SELECT i.id FROM clinical_order_items i JOIN clinical_orders o ON o.id = i.order_id
                WHERE i.id = CAST(:id AS UUID) AND o.order_type = 'medication'
                  AND o.status NOT IN ('completed', 'cancelled') AND i.status <> 'cancelled';
            """), {"id": order_item_id}).first()
            if not item:
                return None
            row = conn.execute(text("""
                INSERT INTO medication_dispenses (order_item_id, dispensed_by, quantity, unit, batch_number, expiry_date, notes)
                VALUES (CAST(:order_item_id AS UUID), :dispensed_by, :quantity, :unit, :batch_number, :expiry_date, :notes)
                RETURNING id::text, order_item_id::text, dispensed_by, quantity, unit, batch_number, expiry_date, status, dispensed_at, notes;
            """), {**data, "order_item_id": order_item_id, "dispensed_by": dispensed_by}).mappings().one()
        return dict(row)

    def record_medication_administration(self, order_item_id: str, data: dict[str, Any], administered_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        if not administered_by:
            return None
        with engine.begin() as conn:
            item = conn.execute(text("""
                SELECT i.id, o.patient_id FROM clinical_order_items i JOIN clinical_orders o ON o.id = i.order_id
                WHERE i.id = CAST(:id AS UUID) AND o.order_type = 'medication'
                  AND o.status NOT IN ('completed', 'cancelled') AND i.status <> 'cancelled';
            """), {"id": order_item_id}).mappings().first()
            if not item:
                return None
            if data.get("dispense_id"):
                valid_dispense = conn.execute(text("""
                    SELECT id FROM medication_dispenses WHERE id = CAST(:dispense_id AS UUID)
                    AND order_item_id = CAST(:order_item_id AS UUID) AND status = 'dispensed';
                """), {"dispense_id": data["dispense_id"], "order_item_id": order_item_id}).first()
                if not valid_dispense:
                    return None
            row = conn.execute(text("""
                INSERT INTO medication_administrations (
                    order_item_id, dispense_id, administered_by, scheduled_for, dose_quantity, dose_unit, route, status, reason, notes
                ) VALUES (
                    CAST(:order_item_id AS UUID), CAST(:dispense_id AS UUID), :administered_by, :scheduled_for,
                    :dose_quantity, :dose_unit, :route, :status, :reason, :notes
                ) RETURNING id::text, order_item_id::text, dispense_id::text, administered_by, scheduled_for,
                    administered_at, dose_quantity, dose_unit, route, status, reason, notes;
            """), {**data, "order_item_id": order_item_id, "administered_by": administered_by}).mappings().one()
            conn.execute(text("""
                INSERT INTO audit_events (actor_staff_id, action, entity_type, entity_id, patient_id, metadata)
                VALUES (:actor, :action, 'medication_administration', :id, :patient_id, jsonb_build_object('order_item_id', :order_item_id));
            """), {"actor": administered_by, "action": f"medication.{data['status']}", "id": row["id"], "patient_id": item["patient_id"], "order_item_id": order_item_id})
        return dict(row)

    def list_medication_administrations(self, order_item_id: str) -> list[dict[str, Any]]:
        _require_conn()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT id::text, order_item_id::text, dispense_id::text, administered_by, scheduled_for,
                    administered_at, dose_quantity, dose_unit, route, status, reason, notes
                FROM medication_administrations WHERE order_item_id = CAST(:id AS UUID)
                ORDER BY administered_at DESC;
            """), {"id": order_item_id}).mappings().all()
        return [dict(row) for row in rows]

    def get_discharge_summary(self, admission_id: str) -> dict[str, Any] | None:
        _require_conn()
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT id::text, admission_id::text, patient_id, authored_by, status, admission_diagnosis,
                    discharge_diagnosis, hospital_course, procedures_performed, discharge_medications,
                    follow_up_instructions, condition_at_discharge, created_at, updated_at, finalized_at
                FROM discharge_summaries WHERE admission_id = CAST(:id AS UUID);
            """), {"id": admission_id}).mappings().first()
        return dict(row) if row else None

    def upsert_discharge_summary(self, admission_id: str, data: dict[str, Any], authored_by: str | None) -> dict[str, Any] | None:
        _require_conn()
        if not authored_by:
            return None
        with engine.begin() as conn:
            admission = conn.execute(text("SELECT patient_id FROM admissions WHERE id = CAST(:id AS UUID) AND status = 'admitted' FOR UPDATE"), {"id": admission_id}).mappings().first()
            if not admission:
                return None
            finalize = bool(data.pop("finalize"))
            current = conn.execute(text("SELECT id, status FROM discharge_summaries WHERE admission_id = CAST(:id AS UUID) FOR UPDATE"), {"id": admission_id}).mappings().first()
            if current and current["status"] == "final":
                return None
            params = {**data, "admission_id": admission_id, "patient_id": admission["patient_id"], "authored_by": authored_by, "status": "final" if finalize else "draft"}
            if current:
                row = conn.execute(text("""
                    UPDATE discharge_summaries SET authored_by = :authored_by, status = :status,
                        admission_diagnosis = :admission_diagnosis, discharge_diagnosis = :discharge_diagnosis,
                        hospital_course = :hospital_course, procedures_performed = :procedures_performed,
                        discharge_medications = :discharge_medications, follow_up_instructions = :follow_up_instructions,
                        condition_at_discharge = :condition_at_discharge, updated_at = NOW(),
                        finalized_at = CASE WHEN :status = 'final' THEN NOW() ELSE NULL END
                    WHERE admission_id = CAST(:admission_id AS UUID)
                    RETURNING id::text, admission_id::text, patient_id, authored_by, status, discharge_diagnosis,
                        hospital_course, discharge_medications, follow_up_instructions, finalized_at, updated_at;
                """), params).mappings().one()
            else:
                row = conn.execute(text("""
                    INSERT INTO discharge_summaries (admission_id, patient_id, authored_by, status,
                        admission_diagnosis, discharge_diagnosis, hospital_course, procedures_performed,
                        discharge_medications, follow_up_instructions, condition_at_discharge, finalized_at)
                    VALUES (CAST(:admission_id AS UUID), :patient_id, :authored_by, :status,
                        :admission_diagnosis, :discharge_diagnosis, :hospital_course, :procedures_performed,
                        :discharge_medications, :follow_up_instructions, :condition_at_discharge,
                        CASE WHEN :status = 'final' THEN NOW() ELSE NULL END)
                    RETURNING id::text, admission_id::text, patient_id, authored_by, status, discharge_diagnosis,
                        hospital_course, discharge_medications, follow_up_instructions, finalized_at, created_at;
                """), params).mappings().one()
            conn.execute(text("""
                INSERT INTO audit_events (actor_staff_id, action, entity_type, entity_id, patient_id, metadata)
                VALUES (:actor, :action, 'discharge_summary', :id, :patient_id, jsonb_build_object('admission_id', :admission_id));
            """), {"actor": authored_by, "action": "discharge_summary.finalized" if finalize else "discharge_summary.saved", "id": row["id"], "patient_id": admission["patient_id"], "admission_id": admission_id})
        return dict(row)


store = DbStore()
