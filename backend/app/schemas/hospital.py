from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    specialty: str | None = Field(default=None, max_length=120)


class LocationCreate(BaseModel):
    department_id: str | None = None
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    location_type: str = Field(pattern=r"^(outpatient_clinic|emergency_unit|ward|theatre|laboratory|pharmacy)$")


class BedCreate(BaseModel):
    location_id: str
    code: str = Field(min_length=1, max_length=32)
    bed_class: str = Field(default="standard", max_length=60)


class AdmissionCreate(BaseModel):
    patient_id: str
    source_visit_id: str | None = None
    admitting_department_id: str | None = None
    attending_doctor_id: str | None = None
    admission_type: str = Field(pattern=r"^(emergency|elective|transfer)$")
    admission_reason: str = Field(min_length=3, max_length=2000)


class BedAssignmentCreate(BaseModel):
    bed_id: str
    reason: str | None = Field(default=None, max_length=500)


class DischargeCreate(BaseModel):
    discharge_disposition: str = Field(min_length=2, max_length=250)


class NursingObservationCreate(BaseModel):
    temperature_c: float | None = Field(default=None, ge=25, le=45)
    pulse_rate: int | None = Field(default=None, ge=0, le=300)
    respiratory_rate: int | None = Field(default=None, ge=0, le=150)
    systolic_bp: int | None = Field(default=None, ge=0, le=300)
    diastolic_bp: int | None = Field(default=None, ge=0, le=250)
    oxygen_saturation: float | None = Field(default=None, ge=0, le=100)
    pain_score: int | None = Field(default=None, ge=0, le=10)
    notes: str | None = Field(default=None, max_length=5000)
