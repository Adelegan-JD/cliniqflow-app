from datetime import datetime, date

from pydantic import BaseModel, Field, model_validator


class MedicationDispenseCreate(BaseModel):
    quantity: float = Field(gt=0, le=1_000_000)
    unit: str = Field(min_length=1, max_length=50)
    batch_number: str | None = Field(default=None, max_length=100)
    expiry_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class MedicationAdministrationCreate(BaseModel):
    scheduled_for: datetime | None = None
    status: str = Field(pattern=r"^(given|held|refused|missed|not_available)$")
    dose_quantity: float | None = Field(default=None, gt=0, le=1_000_000)
    dose_unit: str | None = Field(default=None, max_length=50)
    route: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)
    dispense_id: str | None = None

    @model_validator(mode="after")
    def require_safe_documentation(self):
        if self.status == "given" and (self.dose_quantity is None or not self.dose_unit):
            raise ValueError("dose_quantity and dose_unit are required when medication is given")
        if self.status != "given" and not self.reason:
            raise ValueError("reason is required when medication is not given")
        return self
