"""
module: Defines all Pydantic models for structured clinical data.
Every field has a clear type, optionality, and description.
This is the single source of truth for data shapes across the pipeline.

"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator



# Enums

class Severity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    HIGH = "high"       # >= 0.85
    MEDIUM = "medium"   # 0.60 – 0.84
    LOW = "low"         # < 0.60


class SOAPSection(str, Enum):
    SUBJECTIVE = "subjective"
    OBJECTIVE = "objective"
    ASSESSMENT = "assessment"
    PLAN = "plan"


class ExtractionMethod(str, Enum):
    LLM = "llm"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"



# Sub-models

class Symptom(BaseModel):
    name: str = Field(..., description="Normalised symptom name, e.g. 'fever'")
    raw_text: str = Field(..., description="Exact phrase from transcript")
    duration: Optional[str] = Field(None, description="Duration string, e.g. '3 days'")
    severity: Optional[Severity] = Field(None, description="Assessed severity")
    onset: Optional[str] = Field(None, description="Onset description, e.g. 'sudden'")
    location: Optional[str] = Field(None, description="Body location if mentioned")
    modifiers: List[str] = Field(default_factory=list, description="Additional descriptors")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence 0-1")

    @validator("name")
    def normalise_name(cls, v: str) -> str:
        return v.strip().lower()


class VitalSign(BaseModel):
    name: str = Field(..., description="e.g. 'Blood Pressure', 'Heart Rate', 'Temperature'")
    value: str = Field(..., description="e.g. '98.6', '155/98'")
    unit: Optional[str] = Field(None, description="e.g. 'mmHg', 'bpm', '°C'")
    normal_range: Optional[str] = Field(None, description="e.g. '120/80', '60-100'")
    is_abnormal: bool = Field(False, description="True if value falls outside normal range")


class PatientDemographics(BaseModel):
    age: Optional[str] = Field(None, description="Age string, e.g. '5 years', '8 months', '52'")
    sex: Optional[str] = Field(None, description="'male' | 'female' | 'unknown'")
    weight_kg: Optional[float] = Field(None, description="Weight in kg if mentioned")
    height_cm: Optional[float] = Field(None, description="Height in cm if mentioned")
    bmi: Optional[float] = Field(None, description="Body Mass Index, auto-calculated if weight & height available")


class AllergyRecord(BaseModel):
    substance: str
    reaction: Optional[str] = None
    severity: Optional[Severity] = None


class MedicalHistory(BaseModel):
    past_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[AllergyRecord] = Field(default_factory=list)
    immunisation_status: Optional[str] = None
    family_history: List[str] = Field(default_factory=list)


class ClinicalFlag(BaseModel):
    flag_type: str = Field(..., description="e.g. 'danger_sign', 'urgent_referral'")
    description: str
    severity: Severity
    triggered_by: str = Field(..., description="Symptom or finding that triggered this flag")



# Core structured output

class StructuredClinicalData(BaseModel):
    """
    Primary output of extraction pipeline.
    Contains all structured information extracted from the transcript.
    """
    session_id: str = Field(..., description="Unique session identifier")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_method: ExtractionMethod = ExtractionMethod.HYBRID

    # Patient info
    demographics: PatientDemographics = Field(default_factory=PatientDemographics)
    history: MedicalHistory = Field(default_factory=MedicalHistory)

    # Clinical content
    chief_complaint: str = Field("", description="Primary reason for visit")
    symptoms: List[Symptom] = Field(default_factory=list)
    vital_signs: List[VitalSign] = Field(default_factory=list)
    clinical_flags: List[ClinicalFlag] = Field(default_factory=list)

    # Quality metadata
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Aggregate confidence across all extractions (0-1)")
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    missing_fields: List[str] = Field(default_factory=list, description="e.g. 'Smoking history', 'ECG results'")
    extraction_warnings: List[str] = Field(default_factory=list, description="e.g. 'Radiation of chest pain not mentioned'")
    raw_transcript: str = Field("", description="Original transcript text")

    @validator("confidence_level", always=True, pre=False)
    def set_confidence_level(cls, v: ConfidenceLevel, values: Dict[str, Any]) -> ConfidenceLevel:
        score = values.get("overall_confidence", 0.0)
        if score >= 0.85:
            return ConfidenceLevel.HIGH
        elif score >= 0.60:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW



# SOAP Note model

class SOAPNote(BaseModel):
    """
    Standard SOAP note structure generated from StructuredClinicalData.
    """
    session_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    subjective: str = Field("", description="Patient-reported symptoms and history")
    objective: str = Field("", description="Measurable findings, vitals, observations")
    assessment: str = Field("", description="Clinical summary — NO diagnosis, NO treatment")
    plan: str = Field("", description="Suggested next steps — NO prescription decisions")

    # Metadata
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    flags: List[ClinicalFlag] = Field(default_factory=list, description="Clinical flags extracted from structured data")
    disclaimer: str = Field(
        "This SOAP note is AI-generated for pre-consultation support only. "
        "It does not constitute a diagnosis or treatment plan. "
        "All clinical decisions must be made by a licensed healthcare provider.",
        description="Mandatory safety disclaimer"
    )
    word_count: int = Field(0, description="Total word count across all SOAP sections")

    @validator("word_count", always=True, pre=False)
    def compute_word_count(cls, v: int, values: Dict[str, Any]) -> int:
        total = 0
        for section in ["subjective", "objective", "assessment", "plan"]:
            total += len(values.get(section, "").split())
        return total



# Validation result model

class ValidationResult(BaseModel):
    is_valid: bool
    session_id: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    requires_fallback: bool = False
    validated_at: datetime = Field(default_factory=datetime.utcnow)



# API request / response wrappers

class NLPRequest(BaseModel):
    session_id: str
    transcript: str = Field(..., min_length=1)
    patient_age: Optional[str] = None
    patient_sex: Optional[str] = None


class NLPResponse(BaseModel):
    session_id: str
    structured_data: StructuredClinicalData
    soap_note: SOAPNote
    validation: ValidationResult
    processing_time_ms: float = 0.0
