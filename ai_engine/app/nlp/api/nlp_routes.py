"""
API endpoints with THREE workflows:
1. Nurse enters vitals → gets urgency badge
2. Nurse sends to doctor → doctor gets complete SOAP with nurse vitals in Objective
3. Doctor full pipeline (legacy - kept for compatibility)
"""

from __future__ import annotations
import time
import uuid
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models.clinical_schema import PatientDemographics, VitalSign, StructuredClinicalData, ExtractionMethod, MedicalHistory
from ..src.urgency_scorer import UrgencyScorer
from ..src.symptom_extractor import SymptomExtractor
from ..src.soap_formatter import SOAPFormatter
from ..src.validators import ClinicalValidator

router = APIRouter(prefix="/nlp", tags=["NLP & Clinical Structuring"])

# Initialize services
_extractor = SymptomExtractor()
_formatter = SOAPFormatter()
_validator = ClinicalValidator()
_urgency_scorer = UrgencyScorer()



# NURSE ENTERS VITALS → GETS URGENCY


class NurseVitalsInput(BaseModel):
    """Nurse enters vital signs only."""
    patient_age: str = Field(..., example="5 years")
    patient_sex: str = Field(..., example="male")
    temperature: float = Field(..., ge=30.0, le=45.0, example=37.2)
    heart_rate: int = Field(..., ge=40, le=250, example=100)
    respiratory_rate: int = Field(..., ge=8, le=80, example=20)
    oxygen_saturation: Optional[float] = Field(None, ge=70.0, le=100.0, example=98.0)
    weight_kg: Optional[float] = Field(None, gt=0, le=200, example=18.5)
    height_cm: Optional[float] = Field(None, gt=0, le=250, example=110.0)
    session_id: Optional[str] = None


class VitalsUrgencyResponse(BaseModel):
    """Response with urgency level."""
    session_id: str
    urgency_level: str
    urgency_score: int
    urgency_reasons: List[str]
    abnormal_vitals: List[str]
    bmi: Optional[float]
    bmi_category: Optional[str]
    vitals: List[dict]
    patient_age: str
    patient_sex: str
    processing_time_ms: float


def _assess_bmi(bmi: float) -> str:
    """WHO-style BMI classification"""
    if bmi < 16:
        return "Severe Underweight"
    elif bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


@router.post("/vitals-urgency", response_model=VitalsUrgencyResponse)
async def calculate_vitals_urgency(input: NurseVitalsInput) -> VitalsUrgencyResponse:
    """
    NURSE WORKFLOW: Calculate urgency from vitals.
    """
    session_id = input.session_id or f"vitals-{int(time.time() * 1000)}"
    start = time.perf_counter()

    try:
        # UrgencyScorer will handle ALL logic (WHO + age-aware)

        vitals = [
            VitalSign(name="temperature", value=str(input.temperature), unit="°C"),
            VitalSign(name="heart_rate", value=str(input.heart_rate), unit="bpm"),
            VitalSign(name="respiratory_rate", value=str(input.respiratory_rate), unit="breaths/min"),
        ]

        # OPTIONAL vital
        if input.oxygen_saturation is not None:
            vitals.append(
                VitalSign(
                    name="oxygen_saturation",
                    value=str(input.oxygen_saturation),
                    unit="%"
                )
            )

        # BMI calculation
        bmi = None
        bmi_category = "Unknown"

        if input.weight_kg is not None and input.height_cm is not None:
            height_m = input.height_cm / 100
            bmi = input.weight_kg / (height_m ** 2)
            bmi_category = _assess_bmi(bmi)

        demographics = PatientDemographics(
            age=input.patient_age,
            sex=input.patient_sex,
            weight_kg=input.weight_kg,
            height_cm=input.height_cm,
            bmi=bmi,
        )

        # MAIN SCORING (single source of truth)
        urgency = _urgency_scorer.score(vitals, demographics)

        # derive abnormal vitals FROM scorer
        abnormal_set = set(urgency.abnormal_vitals)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return VitalsUrgencyResponse(
            session_id=session_id,
            urgency_level=urgency.level.value,
            urgency_score=urgency.score,
            urgency_reasons=urgency.reasons,
            abnormal_vitals=urgency.abnormal_vitals,
            bmi=round(bmi, 2) if bmi is not None else None,
            bmi_category=bmi_category,

            # build response vitals dynamically
            vitals=[
                {
                    "name": v.name,
                    "value": v.value,
                    "unit": v.unit,
                    "is_abnormal": v.name in abnormal_set,
                }
                for v in vitals
            ],

            patient_age=input.patient_age,
            patient_sex=input.patient_sex,
            processing_time_ms=round(elapsed_ms, 2),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate urgency: {str(e)}")



# NURSE → DOCTOR HANDOFF


class NurseToDoctorHandoff(BaseModel):
    session_id: str
    patient_age: str
    patient_sex: str

    temperature: float
    heart_rate: int
    respiratory_rate: int
    oxygen_saturation: float
    weight_kg: float
    height_cm: float

    urgency_level: str
    urgency_score: int

    transcript: Optional[str] = None


@router.post("/nurse-to-doctor")
async def nurse_to_doctor_handoff(input: NurseToDoctorHandoff):
    start = time.perf_counter()

    try:
        
        nurse_vitals = [
            VitalSign(name="temperature", value=str(input.temperature), unit="°C"),
            VitalSign(name="heart_rate", value=str(input.heart_rate), unit="bpm"),
            VitalSign(name="respiratory_rate", value=str(input.respiratory_rate), unit="breaths/min"),
            VitalSign(name="oxygen_saturation", value=str(input.oxygen_saturation), unit="%"),
        ]

        # Extract or fallback
        if input.transcript and len(input.transcript.strip()) > 5:
            structured_data, method = _extractor.extract(
                transcript=input.transcript,
                session_id=input.session_id,
                patient_age=input.patient_age,
                patient_sex=input.patient_sex,
            )
        else:
            height_m = input.height_cm / 100
            bmi = input.weight_kg / (height_m ** 2)

            structured_data = StructuredClinicalData(
                session_id=input.session_id,
                extraction_method=ExtractionMethod.RULE_BASED,
                demographics=PatientDemographics(
                    age=input.patient_age,
                    sex=input.patient_sex,
                    weight_kg=input.weight_kg,
                    height_cm=input.height_cm,
                    bmi=bmi,
                ),
                history=MedicalHistory(),
                chief_complaint="Awaiting doctor consultation",
                symptoms=[],
                vital_signs=nurse_vitals,
                clinical_flags=[],
                overall_confidence=1.0,
                raw_transcript="No transcript provided yet",
            )

        soap_note = _formatter.format(structured_data, nurse_vitals=nurse_vitals)
        validation = _validator.validate_all(structured_data, soap_note)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "session_id": input.session_id,
            "urgency_from_nurse": {
                "level": input.urgency_level,
                "score": input.urgency_score,
            },
            "structured_data": structured_data.dict(),
            "soap_note": soap_note.dict(),
            "validation": validation.dict(),
            "processing_time_ms": round(elapsed_ms, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoff failed: {str(e)}")



# DOCTOR FULL PIPELINE


class FullProcessRequest(BaseModel):
    transcript: str = Field(..., min_length=5)
    patient_age: Optional[str] = None
    patient_sex: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/nlp/process")  # added /nlp prefix
async def process_transcript(request: FullProcessRequest):
    session_id = request.session_id or str(uuid.uuid4())
    start = time.perf_counter()

    structured_data, method = _extractor.extract(
        transcript=request.transcript,
        session_id=session_id,
        patient_age=request.patient_age,
        patient_sex=request.patient_sex,
    )

    soap_note = _formatter.format(structured_data)
    validation = _validator.validate_all(structured_data, soap_note)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "session_id": session_id,
        "structured_data": structured_data.dict(),
        "soap_note": soap_note.dict(),
        "validation": validation.dict(),
        "processing_time_ms": round(elapsed_ms, 2),
    }


# HEALTH CHECK


@router.get("/health")
async def nlp_health():
    return {
        "service": "nlp",
        "status": "healthy",
        "workflows": {
            "nurse_vitals": "POST /nlp/vitals-urgency",
            "nurse_to_doctor": "POST /nlp/nurse-to-doctor",
            "legacy": "POST /nlp/process",
        },
    }