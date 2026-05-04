"""
In-memory persistence until Supabase/Postgres schema is wired.
Domain names only — not final table mappings.
"""

from __future__ import annotations

import itertools
import threading
import uuid
from datetime import date, datetime, timezone
from typing import Any

from app.core.visit_status import (
    COMPLETED,
    WAITING_FOR_DOCTOR,
    WAITING_FOR_TRIAGE,
    WITH_DOCTOR,
    normalize_visit_status,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MemoryStore:
    """Thread-safe singleton-style store for API-first development."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._patient_seq = itertools.count(1)
        self._visit_seq = itertools.count(1)
        self.patients: dict[str, dict[str, Any]] = {}
        self.visits: dict[str, dict[str, Any]] = {}
        self.triage_events: list[dict[str, Any]] = []
        self.examinations: list[dict[str, Any]] = []
        self.users: list[dict[str, Any]] = [
            {
                "id": "seed-admin-1",
                "email": "admin@cliniq.local",
                "name": "System Admin",
                "role": "admin",
            },
            {
                "id": "seed-doc-1",
                "email": "doctor@cliniq.local",
                "name": "Demo Doctor",
                "role": "doctor",
            },
        ]

    def next_pid(self) -> str:
        n = next(self._patient_seq)
        return f"PID-{date.today().year}-{n:05d}"

    def next_visit_id(self) -> str:
        n = next(self._visit_seq)
        return f"VS-{date.today().year}-{n:05d}"

    def register_patient(
        self, data: dict[str, Any], registered_by: str | None = None
    ) -> dict[str, Any]:
        with self._lock:
            pid = self.next_pid()
            uid = str(uuid.uuid4())
            row = {
                "id": uid,
                "pid": pid,
                "created_at": _utcnow().isoformat(),
                **data,
            }
            if registered_by:
                row["registered_by"] = registered_by
            self.patients[uid] = row
            return row

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        return self.patients.get(patient_id)

    def list_patients(self, search: str | None = None) -> list[dict[str, Any]]:
        rows = list(self.patients.values())
        if not search:
            return rows
        q = search.lower()
        out = []
        for p in rows:
            name = f"{p.get('firstName', '')} {p.get('lastName', '')}".lower()
            pid = (p.get("pid") or "").lower()
            phone = (p.get("phone") or "").lower()
            if q in name or q in pid or q in phone:
                out.append(p)
        return out

    def search_patients(
        self, q: str, search_by: str
    ) -> list[dict[str, Any]]:
        q = q.strip().lower()
        results: list[dict[str, Any]] = []
        for p in self.patients.values():
            if search_by == "pid":
                if q in (p.get("pid") or "").lower():
                    results.append(self._patient_summary(p))
            elif search_by == "phone":
                if q in (p.get("phone") or "").lower():
                    results.append(self._patient_summary(p))
            else:  # nameDob
                name = f"{p.get('firstName', '')} {p.get('lastName', '')}".lower()
                dob = (p.get("dob") or "").lower()
                if q in name or q in dob:
                    results.append(self._patient_summary(p))
        return results

    def _patient_summary(self, p: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": p["id"],
            "pid": p.get("pid"),
            "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
            "phone": p.get("phone"),
            "dob": p.get("dob"),
            "gender": p.get("gender"),
        }

    def create_visit(
        self,
        patient_id: str,
        reason_for_visit: str | None,
        department: str | None,
        checked_in_by: str | None = None,
    ) -> dict[str, Any] | None:
        p = self.get_patient(patient_id)
        if not p:
            return None
        with self._lock:
            vid = self.next_visit_id()
            now = _utcnow()
            row = {
                "visit_id": vid,
                "patient_id": patient_id,
                "patient_name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
                "reason_for_visit": reason_for_visit,
                "department": department,
                "visit_status": WAITING_FOR_TRIAGE,
                "triage_status": "PENDING",
                "created_at": now.isoformat(),
            }
            self.visits[vid] = row
            return row

    def get_visit(self, visit_id: str) -> dict[str, Any] | None:
        v = self.visits.get(visit_id)
        if not v:
            return None
        out = dict(v)
        out["visit_status"] = normalize_visit_status(out.get("visit_status"))
        return out

    def list_visits_values(self) -> list[dict[str, Any]]:
        out = []
        for v in self.visits.values():
            row = dict(v)
            row["visit_status"] = normalize_visit_status(row.get("visit_status"))
            out.append(row)
        return out

    def list_visits_for_nurse_queue(self) -> list[dict[str, Any]]:
        """Visits still waiting for triage."""
        out = []
        for v in self.visits.values():
            st = normalize_visit_status(v.get("visit_status"))
            if st != WAITING_FOR_TRIAGE:
                continue
            p = self.get_patient(v["patient_id"])
            out.append(
                {
                    "visit_id": v["visit_id"],
                    "patient_id": v["patient_id"],
                    "patient_name": v.get("patient_name"),
                    "visit_status": st,
                    "triage_status": v.get("triage_status"),
                    "created_at": v.get("created_at"),
                    "age": p.get("age") if p else None,
                    "gender": p.get("gender") if p else None,
                }
            )
        return sorted(out, key=lambda x: x.get("created_at") or "", reverse=True)

    def list_visits_for_doctor_queue(self) -> list[dict[str, Any]]:
        out = []
        for v in self.visits.values():
            st = normalize_visit_status(v.get("visit_status"))
            if st not in (WAITING_FOR_DOCTOR, WITH_DOCTOR):
                continue
            p = self.get_patient(v["patient_id"])
            out.append(
                {
                    "visit_id": v["visit_id"],
                    "patient_id": v["patient_id"],
                    "patient_name": v.get("patient_name"),
                    "visit_status": st,
                    "triage_status": v.get("triage_status"),
                    "created_at": v.get("created_at"),
                    "age": p.get("age") if p else None,
                    "gender": p.get("gender") if p else None,
                }
            )
        return sorted(out, key=lambda x: x.get("created_at") or "", reverse=True)

    def save_triage(
        self,
        visit_id: str,
        patient_id: str,
        vitals: dict[str, Any],
        urgency: str | None,
        nurse_staff_id: str | None = None,
    ) -> dict[str, Any] | None:
        v = self.get_visit(visit_id)
        if not v or v.get("patient_id") != patient_id:
            return None
        p = self.get_patient(patient_id)
        with self._lock:
            v["visit_status"] = WAITING_FOR_DOCTOR
            v["triage_status"] = "COMPLETE"
            v["triage_vitals"] = vitals
            v["urgency_level"] = urgency
            ev = {
                "id": str(uuid.uuid4()),
                "visit_id": visit_id,
                "patient_id": patient_id,
                "pid": p.get("pid") if p else None,
                "name": v.get("patient_name"),
                "age": p.get("age") if p else None,
                "gender": p.get("gender") if p else None,
                "vitals": vitals,
                "urgencyLevel": (urgency or "normal").lower(),
                "triagedAt": _utcnow().strftime("%Y-%m-%d %H:%M"),
                "vitalsSummary": self._vitals_summary(vitals),
            }
            self.triage_events.append(ev)
            return ev

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
        rows = list(self.triage_events)
        if urgency:
            u = urgency.lower()
            rows = [r for r in rows if (r.get("urgencyLevel") or "").lower() == u]
        if search:
            s = search.lower()
            rows = [
                r
                for r in rows
                if s in (r.get("name") or "").lower()
                or s in (r.get("pid") or "").lower()
            ]
        return list(reversed(rows))

    def save_visit_encounter(
        self,
        visit_id: str,
        patient_id: str | None,
        transcript: str,
        soap: dict[str, str],
        prescriptions: list[dict[str, Any]],
        doctor_notes: str | None,
        doctor_staff_id: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            v = self.visits.get(visit_id)
            if v:
                v["visit_status"] = COMPLETED
                v["completed_at"] = _utcnow().isoformat()
            p = self.get_patient(patient_id) if patient_id else None
            triage_data = None
            if v and v.get("triage_vitals"):
                tv = v["triage_vitals"]
                triage_data = {
                    "vitals": tv,
                    "urgency_level": (v.get("urgency_level") or "normal").lower(),
                }
            ex_id = str(uuid.uuid4())
            now = _utcnow()
            ex = {
                "id": ex_id,
                "visit_id": visit_id,
                "patient_id": patient_id,
                "patient_name": (v.get("patient_name") if v else None)
                or (
                    f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
                    if p
                    else None
                ),
                "pid": p.get("pid") if p else None,
                "age": p.get("age") if p else None,
                "gender": p.get("gender") if p else None,
                "date_of_birth": p.get("dob") if p else None,
                "phone_number": p.get("phone") if p else None,
                "created_at": now.isoformat(),
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
            self.examinations.append(ex)
            return ex

    def list_examinations(self) -> list[dict[str, Any]]:
        return list(reversed(self.examinations.copy()))

    def start_exam(self, visit_id: str) -> dict[str, Any] | None:
        """Mark visit as doctor in room (from WAITING_FOR_DOCTOR)."""
        v = self.visits.get(visit_id)
        if not v:
            return None
        st = normalize_visit_status(v.get("visit_status"))
        if st != WAITING_FOR_DOCTOR:
            return None
        with self._lock:
            v["visit_status"] = WITH_DOCTOR
        return self.get_visit(visit_id)

    def cancel_exam(self, visit_id: str) -> dict[str, Any] | None:
        """Return visit to doctor queue without saving (from WITH_DOCTOR)."""
        v = self.visits.get(visit_id)
        if not v:
            return None
        st = normalize_visit_status(v.get("visit_status"))
        if st != WITH_DOCTOR:
            return None
        with self._lock:
            v["visit_status"] = WAITING_FOR_DOCTOR
        return self.get_visit(visit_id)

    def doctor_dashboard_stats(self) -> dict[str, int]:
        today = date.today().isoformat()
        visits_today = [
            v for v in self.visits.values() if (v.get("created_at") or "").startswith(today)
        ]
        return {
            "totalPatientsToday": len(visits_today),
            "awaitingTriage": len(
                [
                    v
                    for v in self.visits.values()
                    if normalize_visit_status(v.get("visit_status")) == WAITING_FOR_TRIAGE
                ]
            ),
            "awaitingConsultation": len(
                [
                    v
                    for v in self.visits.values()
                    if normalize_visit_status(v.get("visit_status"))
                    in (WAITING_FOR_DOCTOR, WITH_DOCTOR)
                ]
            ),
            "visitsEnded": len(
                [
                    v
                    for v in self.visits.values()
                    if normalize_visit_status(v.get("visit_status")) == COMPLETED
                ]
            ),
        }

    def record_officer_dashboard(self) -> dict[str, Any]:
        today = date.today().isoformat()
        visits_today = [v for v in self.visits.values() if (v.get("created_at") or "").startswith(today)]
        regs_today = [
            p
            for p in self.patients.values()
            if (p.get("created_at") or "").startswith(today)
        ]
        waiting = [
            v
            for v in self.visits.values()
            if normalize_visit_status(v.get("visit_status")) == WAITING_FOR_TRIAGE
        ]
        recent_visits = sorted(
            self.visits.values(),
            key=lambda x: x.get("created_at") or "",
            reverse=True,
        )[:8]
        recent_regs = sorted(
            self.patients.values(),
            key=lambda x: x.get("created_at") or "",
            reverse=True,
        )[:8]
        return {
            "stats": {
                "visitsToday": len(visits_today),
                "waitingForTriage": len(waiting),
                "newRegistrationsToday": len(regs_today),
            },
            "queue": [
                {
                    "visit_id": v["visit_id"],
                    "patient_name": v.get("patient_name"),
                    "status": v.get("visit_status"),
                    "created_at": v.get("created_at"),
                }
                for v in waiting[:20]
            ],
            "recentVisits": [
                {
                    "visit_id": v["visit_id"],
                    "patient_name": v.get("patient_name"),
                    "visit_status": v.get("visit_status"),
                    "created_at": v.get("created_at"),
                }
                for v in recent_visits
            ],
            "recentRegistrations": [
                {
                    "id": p["id"],
                    "pid": p.get("pid"),
                    "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
                    "created_at": p.get("created_at"),
                }
                for p in recent_regs
            ],
        }

    def list_users_admin(self) -> list[dict[str, Any]]:
        return [
            {
                "id": u.get("id"),
                "name": u.get("name", ""),
                "email": u.get("email", ""),
                "role": u.get("role", ""),
            }
            for u in self.users
        ]

    def admin_stats(self) -> dict[str, int]:
        today = date.today().isoformat()
        visits_today = sum(
            1
            for v in self.visits.values()
            if (v.get("created_at") or "").startswith(today)
        )
        return {
            "totalPatients": len(self.patients),
            "visitsToday": visits_today,
            "newRegistrationsThisMonth": len(self.patients),
            "doctorQueue": len(
                [
                    v
                    for v in self.visits.values()
                    if normalize_visit_status(v.get("visit_status"))
                    in (WAITING_FOR_DOCTOR, WITH_DOCTOR)
                ]
            ),
        }

    def add_user_invite(
        self, email: str, display_name: str, role: str, password: str | None = None
    ) -> dict[str, Any]:
        row = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": display_name,
            "role": role.replace("_", " ").title(),
        }
        with self._lock:
            self.users.append(row)
        return row


store = MemoryStore()
