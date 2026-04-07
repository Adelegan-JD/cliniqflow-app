from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="CliniqFlow Nurse Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientEntry(BaseModel):
    patientId: str
    name: str
    age: int
    sex: str
    status: str
    urgency: Optional[str] = "normal"
    vitals: Optional[dict] = None

class TriageSaveRequest(BaseModel):
    patientId: str
    vitals: dict
    triageStatus: str

class TriageRecord(BaseModel):
    id: str
    patientId: str
    name: str
    age: int
    sex: str
    urgencyLevel: str
    triagedAt: str
    vitals: dict

# In-memory store
triage_queue: List[PatientEntry] = [
    PatientEntry(patientId="PT-002-TO", name="Tunde Okafor", age=41, sex="Male", status="awaiting_triage", urgency="urgent"),
    PatientEntry(patientId="PT-005-CE", name="Chioma Eze", age=22, sex="Female", status="awaiting_triage", urgency="normal"),
    PatientEntry(patientId="PT-007-MA", name="Maryam Abubakar", age=30, sex="Female", status="awaiting_triage", urgency="critical"),
]
triage_records: List[TriageRecord] = []

@app.get("/nurse/stats")
def get_nurse_stats():
    awaiting_triage = sum(1 for p in triage_queue if p.status == "awaiting_triage")
    awaiting_consultation = sum(1 for p in triage_queue if p.status == "triaged")
    total_patients_today = awaiting_triage + awaiting_consultation + len([p for p in triage_records])
    visits_ended = len([p for p in triage_records if p.urgencyLevel == "normal"])  # rough metric

    return {
        "totalPatientsToday": total_patients_today,
        "awaitingTriage": awaiting_triage,
        "awaitingConsultation": awaiting_consultation,
        "visitsEnded": visits_ended,
    }

@app.get("/nurse/triage-queue")
def get_nurse_triage_queue():
    return [p.dict() for p in triage_queue]

@app.get("/nurse/triage-records")
def get_nurse_triage_records(urgency: Optional[str] = None, search: Optional[str] = None):
    result = triage_records
    if urgency:
        result = [r for r in result if r.urgencyLevel == urgency]
    if search:
        q = search.lower()
        result = [r for r in result if q in r.name.lower() or q in r.patientId.lower()]
    return result

def resolve_urgency_from_vitals(vitals: dict) -> str:
    try:
        bp_s = float(vitals.get("bpSystolic", 0))
        bp_d = float(vitals.get("bpDiastolic", 0))
        rr = float(vitals.get("respiratoryRate", 0))
        oxygen = float(vitals.get("oxygenSaturation", 100))
        temp = float(vitals.get("temperature", 0))
    except Exception:
        return "normal"

    if oxygen < 91 or rr > 30 or temp >= 39 or bp_s >= 180 or bp_d >= 120:
        return "emergency"
    if rr > 24 or oxygen < 95 or temp >= 38 or bp_s >= 140 or bp_d >= 90:
        return "urgent"
    return "normal"

@app.post("/nurse/triage")
def post_nurse_triage(payload: TriageSaveRequest):
    patient = next((p for p in triage_queue if p.patientId == payload.patientId), None)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in triage queue")

    urgency = payload.triageStatus or resolve_urgency_from_vitals(payload.vitals)
    patient.status = "triaged"
    patient.urgency = urgency

    record = TriageRecord(
        id=f"rec-{len(triage_records)+1}",
        patientId=patient.patientId,
        name=patient.name,
        age=patient.age,
        sex=patient.sex,
        urgencyLevel=urgency,
        triagedAt=datetime.utcnow().isoformat(),
        vitals=payload.vitals,
    )

    triage_records.append(record)

    return {
        "message": "Triage saved",
        "patient": patient,
        "record": record,
    }

@app.post("/nlp/vitals-urgency")
def resolve_vitals_urgency(data: dict):
    urgency = resolve_urgency_from_vitals(data)
    method = "rule_based"
    return {"urgency_level": urgency, "method": method}
