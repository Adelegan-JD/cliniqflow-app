from pydantic import BaseModel, Field


class DischargeSummaryUpsert(BaseModel):
    admission_diagnosis: str | None = Field(default=None, max_length=10000)
    discharge_diagnosis: str = Field(min_length=2, max_length=10000)
    hospital_course: str = Field(min_length=2, max_length=20000)
    procedures_performed: str | None = Field(default=None, max_length=10000)
    discharge_medications: str | None = Field(default=None, max_length=10000)
    follow_up_instructions: str | None = Field(default=None, max_length=10000)
    condition_at_discharge: str | None = Field(default=None, max_length=1000)
    finalize: bool = False
