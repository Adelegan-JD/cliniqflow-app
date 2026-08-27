from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ClinicalFormTemplateCreate(BaseModel):
    department_id: str | None = None
    code: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    schema_json: dict[str, Any]

    @field_validator("schema_json")
    @classmethod
    def validate_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        fields = value.get("fields")
        if not isinstance(fields, list) or not fields:
            raise ValueError("schema_json must include a non-empty fields list")
        seen: set[str] = set()
        for field in fields:
            if not isinstance(field, dict) or not isinstance(field.get("key"), str) or not field["key"].strip():
                raise ValueError("each schema field needs a non-empty key")
            if field["key"] in seen:
                raise ValueError("schema field keys must be unique")
            seen.add(field["key"])
        return value


class ClinicalFormResponseCreate(BaseModel):
    template_id: str
    patient_id: str
    visit_id: str | None = None
    admission_id: str | None = None
    response_json: dict[str, Any]
    status: str = Field(default="draft", pattern=r"^(draft|final)$")

    @model_validator(mode="after")
    def encounter_required(self):
        if not self.visit_id and not self.admission_id:
            raise ValueError("visit_id or admission_id is required")
        return self
