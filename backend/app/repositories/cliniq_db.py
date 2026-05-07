"""
PostgreSQL-backed store aligned with `database/schema.py`.
Used when `DATABASE_URL` is set (see `app.repositories` package init).
"""

from __future__ import annotations

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

    def list_visits_for_nurse_queue(self) -> list[dict[str, Any]]:
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
                      AND q.current_stage = 'waiting'
                      AND q.status = 'queued'
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
                        "triage_status": "PENDING",
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

    def list_record_officer_today_records(self) -> list[dict[str, Any]]:
        _require_conn()
        today = date.today()
        with engine.connect() as conn:
            rows = conn.execute(
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

        return [
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
            for x in rows
        ]


store = DbStore()
