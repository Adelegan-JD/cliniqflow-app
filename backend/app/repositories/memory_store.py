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
        self.departments: dict[str, dict[str, Any]] = {}
        self.locations: dict[str, dict[str, Any]] = {}
        self.beds: dict[str, dict[str, Any]] = {}
        self.admissions: dict[str, dict[str, Any]] = {}
        self.bed_assignments: list[dict[str, Any]] = []
        self.nursing_observations: list[dict[str, Any]] = []
        self.invoices: dict[str, dict[str, Any]] = {}
        self.payments: dict[str, dict[str, Any]] = {}
        self.clinical_form_templates: dict[str, dict[str, Any]] = {}
        self.clinical_form_responses: list[dict[str, Any]] = []
        self.clinical_orders: dict[str, dict[str, Any]] = {}
        self.clinical_order_items: dict[str, dict[str, Any]] = {}
        self.medication_dispenses: dict[str, dict[str, Any]] = {}
        self.medication_administrations: list[dict[str, Any]] = []
        self.discharge_summaries: dict[str, dict[str, Any]] = {}
        self.dosage_checks: list[dict[str, Any]] = []
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
        
        # Check if patient already has an active visit
        with self._lock:
            for visit in self.visits.values():
                if (visit.get("patient_id") == patient_id and 
                    visit.get("visit_status") in [WAITING_FOR_TRIAGE, "ACTIVE", "ongoing"]):
                    return None  # Patient already has an active visit
            
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

    def record_dosage_check(
        self, visit_id: str | None, requested_by: str | None, request: dict[str, Any], assessment: dict[str, Any]
    ) -> dict[str, Any] | None:
        visit = self.get_visit(visit_id or "")
        if not visit or not requested_by:
            return None
        row = {
            "id": str(uuid.uuid4()), "visit_id": visit_id,
            "patient_id": visit["patient_id"], "requested_by": requested_by,
            "request_payload": request, "assessment_payload": assessment,
            "safety_level": assessment.get("safety_level", "insufficient_data"),
            "evidence_snapshot": assessment.get("evidence", []),
            "created_at": _utcnow().isoformat(),
        }
        with self._lock:
            self.dosage_checks.append(row)
        return row

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
        # Also include patients registered today (new registrations) who do not yet have a visit
        today = date.today().isoformat()
        for pid, patient in self.patients.items():
            created = patient.get("created_at") or ""
            if not created.startswith(today):
                continue
            # skip if there's already a visit for this patient today
            has_visit_today = any(
                (v.get("patient_id") == pid and (v.get("created_at") or "").startswith(today))
                for v in self.visits.values()
            )
            if has_visit_today:
                continue
            out.append(
                {
                    "visit_id": None,
                    "patient_id": pid,
                    "patient_name": f"{patient.get('firstName','')} {patient.get('lastName','')}".strip(),
                    "visit_status": WAITING_FOR_TRIAGE,
                    "triage_status": "PENDING",
                    "created_at": created,
                    "age": patient.get("age"),
                    "gender": patient.get("gender"),
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

    def list_triaged_patients_for_doctor(self) -> list[dict[str, Any]]:
        """Get all patients who have completed triage today and are ready for consultation."""
        out = []
        today = date.today().isoformat()
        for v in self.visits.values():
            st = normalize_visit_status(v.get("visit_status"))
            # Only include patients who have been triaged and are waiting for doctor
            if st not in (WAITING_FOR_DOCTOR, WITH_DOCTOR):
                continue
            # Only include today's visits
            if not (v.get("created_at") or "").startswith(today):
                continue
            p = self.get_patient(v["patient_id"])
            out.append(
                {
                    "visit_id": v["visit_id"],
                    "patient_id": v["patient_id"],
                    "patient_name": v.get("patient_name"),
                    "visit_status": st,
                    "triage_status": "COMPLETE",
                    "urgency_level": (v.get("urgency_level") or "normal").lower(),
                    "triaged_at": v.get("triage_date") or v.get("created_at"),
                    "created_at": v.get("created_at"),
                    "age": p.get("age") if p else None,
                    "gender": p.get("gender") if p else None,
                }
            )
        return sorted(out, key=lambda x: x.get("triaged_at") or "", reverse=True)

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
        completed_today = [
            v
            for v in self.visits.values()
            if normalize_visit_status(v.get("visit_status")) == COMPLETED
            and (v.get("created_at") or "").startswith(today)
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
                "totalPatientsToday": len(regs_today),
                "activeQueueCount": len(waiting),
                "visitsCreatedToday": len(visits_today),
                "completedVisitsToday": len(completed_today),
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

    def list_departments(self) -> list[dict[str, Any]]:
        return list(self.departments.values())

    def create_department(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if any(row["code"].lower() == data["code"].lower() for row in self.departments.values()):
                raise ValueError("Department code already exists")
            row = {"id": str(uuid.uuid4()), "is_active": True, "created_at": _utcnow().isoformat(), **data}
            self.departments[row["id"]] = row
            return row

    def load_starter_catalogue(self, departments: list[tuple[str, str, str]], locations: list[tuple[str, str, str, str | None]]) -> dict[str, int]:
        added_departments = 0
        added_locations = 0
        with self._lock:
            for code, name, specialty in departments:
                if not any(row["code"].lower() == code.lower() for row in self.departments.values()):
                    department_id = str(uuid.uuid4())
                    self.departments[department_id] = {"id": department_id, "code": code, "name": name, "specialty": specialty, "is_active": True, "created_at": _utcnow().isoformat()}
                    added_departments += 1
            by_code = {row["code"]: row["id"] for row in self.departments.values()}
            for code, name, location_type, department_code in locations:
                if not any(row["code"].lower() == code.lower() for row in self.locations.values()):
                    location_id = str(uuid.uuid4())
                    self.locations[location_id] = {"id": location_id, "code": code, "name": name, "location_type": location_type, "department_id": by_code.get(department_code), "is_active": True, "created_at": _utcnow().isoformat()}
                    added_locations += 1
        return {"departments_added": added_departments, "locations_added": added_locations}

    def list_locations(self) -> list[dict[str, Any]]:
        return list(self.locations.values())

    def create_location(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = {"id": str(uuid.uuid4()), "is_active": True, "created_at": _utcnow().isoformat(), **data}
            self.locations[row["id"]] = row
            return row

    def list_beds(self) -> list[dict[str, Any]]:
        return list(self.beds.values())

    def create_bed(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if data["location_id"] not in self.locations:
                raise ValueError("Clinical location not found")
            row = {"id": str(uuid.uuid4()), "status": "available", "created_at": _utcnow().isoformat(), **data}
            self.beds[row["id"]] = row
            return row

    def list_admissions(self) -> list[dict[str, Any]]:
        return sorted(self.admissions.values(), key=lambda row: row["admitted_at"], reverse=True)

    def create_admission(self, data: dict[str, Any], created_by: str | None) -> dict[str, Any] | None:
        patient = self.get_patient(data["patient_id"])
        if patient is None:
            return None
        with self._lock:
            admission_id = str(uuid.uuid4())
            row = {
                "id": admission_id,
                "admission_number": f"ADM-{date.today().year}-{len(self.admissions) + 1:05d}",
                "patient_id": patient.get("pid", data["patient_id"]),
                "status": "admitted",
                "created_by": created_by,
                "admitted_at": _utcnow().isoformat(),
                **data,
            }
            self.admissions[admission_id] = row
            return row

    def assign_bed(self, admission_id: str, bed_id: str, assigned_by: str | None, reason: str | None) -> dict[str, Any] | None:
        with self._lock:
            admission = self.admissions.get(admission_id)
            bed = self.beds.get(bed_id)
            if not admission or admission["status"] != "admitted" or not bed or bed["status"] != "available":
                return None
            now = _utcnow().isoformat()
            for assignment in self.bed_assignments:
                if assignment["admission_id"] == admission_id and assignment.get("released_at") is None:
                    assignment["released_at"] = now
                    assignment["release_reason"] = reason or "transfer"
                    self.beds[assignment["bed_id"]]["status"] = "available"
            bed["status"] = "occupied"
            row = {
                "id": str(uuid.uuid4()), "admission_id": admission_id, "bed_id": bed_id,
                "assigned_by": assigned_by, "assigned_at": now, "reason": reason,
            }
            self.bed_assignments.append(row)
            return row

    def discharge_admission(self, admission_id: str, disposition: str, discharged_by: str | None) -> dict[str, Any] | None:
        with self._lock:
            admission = self.admissions.get(admission_id)
            if not admission or admission["status"] != "admitted":
                return None
            now = _utcnow().isoformat()
            admission.update({"status": "discharged", "discharged_at": now, "discharge_disposition": disposition, "discharged_by": discharged_by})
            for assignment in self.bed_assignments:
                if assignment["admission_id"] == admission_id and assignment.get("released_at") is None:
                    assignment["released_at"] = now
                    assignment["release_reason"] = "discharged"
                    self.beds[assignment["bed_id"]]["status"] = "available"
            return dict(admission)

    def list_nursing_observations(self, admission_id: str) -> list[dict[str, Any]]:
        return [row for row in self.nursing_observations if row["admission_id"] == admission_id]

    def record_nursing_observation(self, admission_id: str, data: dict[str, Any], recorded_by: str | None) -> dict[str, Any] | None:
        with self._lock:
            admission = self.admissions.get(admission_id)
            if not admission or admission["status"] != "admitted" or not recorded_by:
                return None
            row = {"id": str(uuid.uuid4()), "admission_id": admission_id, "recorded_by": recorded_by, "recorded_at": _utcnow().isoformat(), **data}
            self.nursing_observations.append(row)
            return row

    def list_invoices(self) -> list[dict[str, Any]]:
        return sorted(self.invoices.values(), key=lambda row: row["created_at"], reverse=True)

    def list_payments(self) -> list[dict[str, Any]]:
        return sorted(self.payments.values(), key=lambda row: row["created_at"], reverse=True)

    def create_invoice(self, data: dict[str, Any], created_by: str | None) -> dict[str, Any] | None:
        patient = self.get_patient(data["patient_id"])
        if not patient:
            return None
        with self._lock:
            items = []
            subtotal = 0
            for item in data["items"]:
                amount = round(item["quantity"] * item["unit_price_kobo"])
                items.append({**item, "amount_kobo": amount})
                subtotal += amount
            invoice_id = str(uuid.uuid4())
            row = {"id": invoice_id, "invoice_number": f"INV-{date.today().year}-{len(self.invoices) + 1:06d}", "patient_id": patient.get("pid", data["patient_id"]), "status": "issued", "currency": "NGN", "subtotal_kobo": subtotal, "discount_kobo": 0, "total_kobo": subtotal, "items": items, "created_by": created_by, "created_at": _utcnow().isoformat(), **{key: value for key, value in data.items() if key != "items"}}
            self.invoices[invoice_id] = row
            return row

    def record_pending_payment(self, data: dict[str, Any], received_by: str | None) -> dict[str, Any] | None:
        with self._lock:
            invoice = self.invoices.get(data["invoice_id"])
            if not invoice or invoice["status"] not in ("issued", "part_paid"):
                return None
            committed = sum(
                payment["amount_kobo"]
                for payment in self.payments.values()
                if payment["invoice_id"] == invoice["id"] and payment["status"] in ("pending", "confirmed")
            )
            if committed + data["amount_kobo"] > invoice["total_kobo"]:
                return None
            row = {"id": str(uuid.uuid4()), "receipt_number": f"RCT-{date.today().year}-{len(self.payments) + 1:06d}", "status": "pending", "currency": "NGN", "received_by": received_by, "created_at": _utcnow().isoformat(), **data}
            self.payments[row["id"]] = row
            return row

    def confirm_payment(self, payment_id: str, confirmed_by: str | None) -> dict[str, Any] | None:
        with self._lock:
            payment = self.payments.get(payment_id)
            if not payment or payment["status"] != "pending":
                return None
            invoice = self.invoices[payment["invoice_id"]]
            payment.update({"status": "confirmed", "received_at": _utcnow().isoformat(), "confirmed_by": confirmed_by})
            paid = sum(p["amount_kobo"] for p in self.payments.values() if p["invoice_id"] == invoice["id"] and p["status"] == "confirmed")
            invoice["status"] = "paid" if paid >= invoice["total_kobo"] else "part_paid"
            return dict(payment)

    def list_clinical_form_templates(self) -> list[dict[str, Any]]:
        return [row for row in self.clinical_form_templates.values() if row["is_active"]]

    def create_clinical_form_template(self, data: dict[str, Any], created_by: str | None) -> dict[str, Any]:
        with self._lock:
            row = {"id": str(uuid.uuid4()), "version": 1, "is_active": True, "created_by": created_by, "created_at": _utcnow().isoformat(), **data}
            self.clinical_form_templates[row["id"]] = row
            return row

    def create_clinical_form_response(self, data: dict[str, Any], recorded_by: str | None) -> dict[str, Any] | None:
        template = self.clinical_form_templates.get(data["template_id"])
        patient = self.get_patient(data["patient_id"])
        if not template or not patient or not recorded_by:
            return None
        row = {"id": str(uuid.uuid4()), "template_version": template["version"], "recorded_by": recorded_by, "created_at": _utcnow().isoformat(), **data}
        self.clinical_form_responses.append(row)
        return row

    def list_clinical_form_responses(self, patient_id: str) -> list[dict[str, Any]]:
        return [row for row in self.clinical_form_responses if row["patient_id"] == patient_id]

    def list_clinical_orders(self, patient_id: str) -> list[dict[str, Any]]:
        return [row for row in self.clinical_orders.values() if row["patient_id"] == patient_id]

    def list_order_worklist(self, order_type: str) -> list[dict[str, Any]]:
        return [row for row in self.clinical_orders.values() if row["order_type"] == order_type and row["status"] not in ("completed", "cancelled")]

    def create_clinical_order(self, data: dict[str, Any], ordered_by: str | None) -> dict[str, Any] | None:
        patient = self.get_patient(data["patient_id"])
        if not patient or not ordered_by:
            return None
        with self._lock:
            order_id = str(uuid.uuid4())
            items = []
            for item in data["items"]:
                item_row = {"id": str(uuid.uuid4()), "order_id": order_id, "status": "requested", **item}
                self.clinical_order_items[item_row["id"]] = item_row
                items.append(item_row)
            row = {"id": order_id, "order_number": f"ORD-{date.today().year}-{len(self.clinical_orders) + 1:06d}", "patient_id": patient.get("pid", data["patient_id"]), "ordered_by": ordered_by, "ordered_at": _utcnow().isoformat(), "status": "requested", "items": items, **{key: value for key, value in data.items() if key != "items"}}
            self.clinical_orders[order_id] = row
            return row

    def update_clinical_order_status(self, order_id: str, data: dict[str, Any], updated_by: str | None) -> dict[str, Any] | None:
        with self._lock:
            order = self.clinical_orders.get(order_id)
            if not order or order["status"] in ("completed", "cancelled"):
                return None
            order.update({"status": data["status"], "updated_by": updated_by})
            if data["status"] == "cancelled":
                order.update({"cancelled_at": _utcnow().isoformat(), "cancelled_by": updated_by, "cancellation_reason": data["cancellation_reason"]})
            return dict(order)

    def record_order_item_result(self, item_id: str, data: dict[str, Any], resulted_by: str | None) -> dict[str, Any] | None:
        with self._lock:
            item = self.clinical_order_items.get(item_id)
            if not item or item["status"] == "cancelled":
                return None
            item.update({"status": "completed", "resulted_by": resulted_by, "resulted_at": _utcnow().isoformat(), **data})
            return dict(item)

    def _is_medication_item(self, item_id: str) -> bool:
        item = self.clinical_order_items.get(item_id)
        return bool(item and self.clinical_orders.get(item["order_id"], {}).get("order_type") == "medication")

    def dispense_medication(self, order_item_id: str, data: dict[str, Any], dispensed_by: str | None) -> dict[str, Any] | None:
        if not dispensed_by or not self._is_medication_item(order_item_id):
            return None
        with self._lock:
            row = {"id": str(uuid.uuid4()), "order_item_id": order_item_id, "dispensed_by": dispensed_by, "status": "dispensed", "dispensed_at": _utcnow().isoformat(), **data}
            self.medication_dispenses[row["id"]] = row
            return row

    def record_medication_administration(self, order_item_id: str, data: dict[str, Any], administered_by: str | None) -> dict[str, Any] | None:
        if not administered_by or not self._is_medication_item(order_item_id):
            return None
        dispense_id = data.get("dispense_id")
        if dispense_id and self.medication_dispenses.get(dispense_id, {}).get("order_item_id") != order_item_id:
            return None
        with self._lock:
            row = {"id": str(uuid.uuid4()), "order_item_id": order_item_id, "administered_by": administered_by, "administered_at": _utcnow().isoformat(), **data}
            self.medication_administrations.append(row)
            return row

    def list_medication_administrations(self, order_item_id: str) -> list[dict[str, Any]]:
        return [row for row in self.medication_administrations if row["order_item_id"] == order_item_id]

    def get_discharge_summary(self, admission_id: str) -> dict[str, Any] | None:
        return self.discharge_summaries.get(admission_id)

    def upsert_discharge_summary(self, admission_id: str, data: dict[str, Any], authored_by: str | None) -> dict[str, Any] | None:
        with self._lock:
            admission = self.admissions.get(admission_id)
            if not admission or not authored_by:
                return None
            existing = self.discharge_summaries.get(admission_id)
            if existing and existing["status"] == "final":
                return None
            status = "final" if data.pop("finalize") else "draft"
            row = {
                "id": existing["id"] if existing else str(uuid.uuid4()), "admission_id": admission_id,
                "patient_id": admission["patient_id"], "authored_by": authored_by, "status": status,
                "created_at": existing["created_at"] if existing else _utcnow().isoformat(),
                "updated_at": _utcnow().isoformat(), **data,
            }
            if status == "final":
                row["finalized_at"] = _utcnow().isoformat()
            self.discharge_summaries[admission_id] = row
            return row


store = MemoryStore()
