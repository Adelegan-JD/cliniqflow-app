"""Request bodies for proxy routes to the AI service (coordinate JSON shape with the ML team)."""

from typing import Any

from pydantic import BaseModel, Field


class VitalsUrgencyRequest(BaseModel):
    patient_age: str | None = None
    patient_sex: str = "unknown"
    temperature: float | None = None
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    oxygen_saturation: float | None = None
    weight_kg: float | None = None
    height_cm: float | None = None
