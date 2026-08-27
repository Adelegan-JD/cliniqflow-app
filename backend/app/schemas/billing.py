from pydantic import BaseModel, Field, model_validator


class InvoiceItemCreate(BaseModel):
    description: str = Field(min_length=2, max_length=500)
    quantity: float = Field(default=1, gt=0, le=10000)
    unit_price_kobo: int = Field(ge=0)
    service_code: str | None = Field(default=None, max_length=64)


class InvoiceCreate(BaseModel):
    patient_id: str
    visit_id: str | None = None
    admission_id: str | None = None
    billing_account_id: str | None = None
    items: list[InvoiceItemCreate] = Field(min_length=1, max_length=100)


class PaymentCreate(BaseModel):
    invoice_id: str
    amount_kobo: int = Field(gt=0)
    method: str = Field(pattern=r"^(cash|bank_transfer|pos|online|insurance_claim)$")
    provider_name: str | None = Field(default=None, max_length=120)
    provider_reference: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def provider_reference_required_for_non_cash(self):
        if self.method != "cash" and not self.provider_reference:
            raise ValueError("provider_reference is required for non-cash payments")
        return self
