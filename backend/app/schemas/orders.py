from typing import Any

from pydantic import BaseModel, Field, model_validator


class ClinicalOrderItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    item_code: str | None = Field(default=None, max_length=64)
    details_json: dict[str, Any] = Field(default_factory=dict)


class ClinicalOrderCreate(BaseModel):
    patient_id: str
    visit_id: str | None = None
    admission_id: str | None = None
    order_type: str = Field(pattern=r"^(laboratory|imaging|procedure|medication)$")
    priority: str = Field(default="routine", pattern=r"^(routine|urgent|stat)$")
    department_id: str | None = None
    clinical_indication: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)
    items: list[ClinicalOrderItemCreate] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def requires_encounter(self):
        if not self.visit_id and not self.admission_id:
            raise ValueError("visit_id or admission_id is required")
        return self


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(accepted|in_progress|completed|cancelled)$")
    cancellation_reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def cancellation_reason_required(self):
        if self.status == "cancelled" and not self.cancellation_reason:
            raise ValueError("cancellation_reason is required when cancelling an order")
        return self


class OrderItemResultCreate(BaseModel):
    result_text: str | None = Field(default=None, max_length=10000)
    result_json: dict[str, Any] | None = None
