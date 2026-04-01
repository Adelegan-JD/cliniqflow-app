"""
module: Validates StructuredClinicalData and SOAPNote objects.
Enforces:
  - Required fields are present
  - Confidence thresholds
  - Clinical safety rules (no diagnosis text, no treatment text)
  - Triggers rule-based fallback when LLM output is unreliable
  
"""

from __future__ import annotations

import logging
import re
from typing import List

from models.clinical_schema import (
    ConfidenceLevel,
    SOAPNote,
    StructuredClinicalData,
    ValidationResult,
)

logger = logging.getLogger("cliniq.nlp.validators")


# Safety: phrases that must NOT appear in AI output

FORBIDDEN_DIAGNOSIS_PHRASES = [
    r"\bdiagnos(?:is|ed|e)\b",
    r"\bthe patient has\b",
    r"\bsuffers from\b",
    r"\bconfirmed\b.*\bcondition\b",
    r"\bprescribe\b",
    r"\bprescription\b",
    r"\badminister\b.*\bmg\b",
    r"\bdose\b.*\bmg/kg\b",
    r"\btreat(?:ment|ing|ed)\b.*\bwith\b.*\b(?:drug|medication|antibiotic|antimalarial)\b",
]

FORBIDDEN_TREATMENT_PHRASES = [
    r"\bgive\b.*\bmg\b",
    r"\btake\b.*\btablets?\b",
    r"\boral rehydration\b.*\badminister\b",
    r"\biv\s+fluids?\b",
    r"\bceftriaxone\b",
    r"\bamoxicillin\b",
    r"\bartesunate\b",
    r"\bparacetamol\b.*\bdose\b",
]

REQUIRED_SOAP_FIELDS = ["subjective", "objective", "assessment", "plan"]

MINIMUM_CONFIDENCE_FOR_SOAP = 0.30  # Below this, SOAP note is flagged as unreliable



# Structured data validator

class StructuredDataValidator:
    """Validates StructuredClinicalData fields and quality."""

    def validate(self, data: StructuredClinicalData) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        missing_required: List[str] = []

        # Required field checks
        if not data.session_id:
            errors.append("session_id is missing")

        if not data.chief_complaint or len(data.chief_complaint.strip()) < 3:
            missing_required.append("chief_complaint")
            warnings.append("Chief complaint is missing or too short — ask nurse to document presenting complaint")

        if not data.symptoms:
            missing_required.append("symptoms")
            warnings.append("No symptoms extracted — transcript may be too short or unclear")

        if not data.demographics.age:
            missing_required.append("patient_age")
            warnings.append("Patient age not extracted — required for paediatric dosage context")

        # Confidence threshold checks
        if data.overall_confidence < MINIMUM_CONFIDENCE_FOR_SOAP:
            warnings.append(
                f"Overall confidence ({data.overall_confidence:.0%}) is below minimum threshold. "
                "Manual review is essential."
            )

        if data.overall_confidence < 0.40 and not data.symptoms:
            errors.append(
                "Extraction quality too low to produce reliable output. "
                "Ensure transcript is complete and retry."
            )

        # Symptom quality checks
        for symptom in data.symptoms:
            if not symptom.raw_text:
                warnings.append(f"Symptom '{symptom.name}' has no raw text reference")
            if symptom.confidence < 0.5:
                warnings.append(f"Low confidence ({symptom.confidence:.0%}) for symptom: {symptom.name}")

        # Safety check: no diagnosis in structured fields
        chief_complaint_safe = self._check_safety(data.chief_complaint, "chief_complaint")
        if chief_complaint_safe:
            errors.extend(chief_complaint_safe)

        is_valid = len(errors) == 0
        requires_fallback = (
            data.confidence_level == ConfidenceLevel.LOW
            or len(missing_required) >= 3
        )

        result = ValidationResult(
            is_valid=is_valid,
            session_id=data.session_id,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required,
            confidence_level=data.confidence_level,
            requires_fallback=requires_fallback,
        )

        if not is_valid:
            logger.warning(f"Validation FAILED for session={data.session_id}: {errors}")
        else:
            logger.info(f"Validation PASSED for session={data.session_id} | warnings={len(warnings)}")

        return result

    def _check_safety(self, text: str, field_name: str) -> List[str]:
        """Check that a text field doesn't contain forbidden clinical conclusions."""
        violations = []
        if not text:
            return violations
        text_lower = text.lower()
        for pattern in FORBIDDEN_DIAGNOSIS_PHRASES:
            if re.search(pattern, text_lower):
                violations.append(
                    f"Safety violation in '{field_name}': potential diagnosis language detected. "
                    "Remove diagnostic conclusions from structured output."
                )
                break
        return violations



# SOAP note validator

class SOAPNoteValidator:
    """Validates SOAP note content for completeness and safety."""

    def validate(self, note: SOAPNote, data: StructuredClinicalData) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        missing_required: List[str] = []

        # Required sections
        for section in REQUIRED_SOAP_FIELDS:
            value = getattr(note, section, "")
            if not value or len(value.strip()) < 10:
                missing_required.append(section)
                errors.append(f"SOAP section '{section}' is empty or too short")

        # Safety checks on each section
        for section in REQUIRED_SOAP_FIELDS:
            content = getattr(note, section, "")
            violations = self._check_no_diagnosis(content, section)
            errors.extend(violations)

            treatment_violations = self._check_no_treatment(content, section)
            errors.extend(treatment_violations)

        # Disclaimer must be present
        if not note.disclaimer:
            errors.append("SOAP note disclaimer is missing — this is a mandatory safety requirement")

        # Consistency: SOAP should reference symptoms from structured data
        if data.symptoms and note.subjective:
            subjective_lower = note.subjective.lower()
            mentioned = sum(
                1 for s in data.symptoms
                if s.name.replace("_", " ") in subjective_lower or s.name in subjective_lower
            )
            if mentioned == 0 and data.symptoms:
                warnings.append("SOAP subjective section doesn't reference any extracted symptoms")

        # Flag consistency
        if data.clinical_flags and not note.flags:
            warnings.append("Clinical flags were detected but not included in SOAP note")

        is_valid = len(errors) == 0
        result = ValidationResult(
            is_valid=is_valid,
            session_id=note.session_id,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required,
            confidence_level=note.confidence_level,
            requires_fallback=False,
        )

        if not is_valid:
            logger.error(f"SOAP validation FAILED for session={note.session_id}: {errors}")
        else:
            logger.info(f"SOAP validation PASSED for session={note.session_id}")

        return result

    def _check_no_diagnosis(self, text: str, section_name: str) -> List[str]:
        if not text:
            return []
        text_lower = text.lower()
        # Allow diagnosis language in the disclaimer itself
        if "disclaimer" in text_lower:
            return []
        violations = []
        for pattern in FORBIDDEN_DIAGNOSIS_PHRASES:
            if re.search(pattern, text_lower):
                violations.append(
                    f"Safety: SOAP '{section_name}' contains potential diagnosis language. "
                    "AI must not diagnose patients."
                )
                break
        return violations

    def _check_no_treatment(self, text: str, section_name: str) -> List[str]:
        if not text or section_name == "plan":
            # Plan can suggest clinical review steps but not prescriptions
            return self._check_no_prescriptions(text, section_name)
        text_lower = text.lower()
        violations = []
        for pattern in FORBIDDEN_TREATMENT_PHRASES:
            if re.search(pattern, text_lower):
                violations.append(
                    f"Safety: SOAP '{section_name}' contains potential treatment/prescription language. "
                    "AI must not prescribe treatments."
                )
                break
        return violations

    def _check_no_prescriptions(self, text: str, section_name: str) -> List[str]:
        if not text:
            return []
        text_lower = text.lower()
        violations = []
        for pattern in FORBIDDEN_TREATMENT_PHRASES:
            if re.search(pattern, text_lower):
                violations.append(
                    f"Safety: SOAP '{section_name}' contains prescription-level language. "
                    "Medication decisions must be made by licensed clinicians only."
                )
                break
        return violations



# Rule-based fallback trigger

class FallbackTrigger:
    """
    Determines whether to use rule-based output instead of LLM output.
    Call after extraction if extraction method was LLM or HYBRID.
    """

    FALLBACK_THRESHOLD = 0.50

    def should_fallback(self, validation: ValidationResult, data: StructuredClinicalData) -> bool:
        """Returns True if the system should re-run rule-based extraction."""
        if validation.requires_fallback:
            logger.info(f"Fallback triggered for session={data.session_id}: validation requires_fallback=True")
            return True

        if data.overall_confidence < self.FALLBACK_THRESHOLD and not data.symptoms:
            logger.info(
                f"Fallback triggered for session={data.session_id}: "
                f"low confidence ({data.overall_confidence}) with no symptoms"
            )
            return True

        if len(validation.errors) > 2:
            logger.info(
                f"Fallback triggered for session={data.session_id}: "
                f"too many validation errors ({len(validation.errors)})"
            )
            return True

        return False



# Convenience combined validator

class ClinicalValidator:
    """
    validator: runs both structured data and SOAP validation.
    Returns the SOAP validation result.
    """

    def __init__(self) -> None:
        self.data_validator = StructuredDataValidator()
        self.soap_validator = SOAPNoteValidator()
        self.fallback_trigger = FallbackTrigger()

    def validate_all(
        self,
        data: StructuredClinicalData,
        note: SOAPNote,
    ) -> ValidationResult:
        data_result = self.data_validator.validate(data)
        soap_result = self.soap_validator.validate(note, data)

        # Merge results — surface all issues
        combined_errors = list(dict.fromkeys(data_result.errors + soap_result.errors))
        combined_warnings = list(dict.fromkeys(data_result.warnings + soap_result.warnings))
        combined_missing = list(dict.fromkeys(data_result.missing_required + soap_result.missing_required))

        requires_fallback = self.fallback_trigger.should_fallback(data_result, data)

        return ValidationResult(
            is_valid=len(combined_errors) == 0,
            session_id=data.session_id,
            errors=combined_errors,
            warnings=combined_warnings,
            missing_required=combined_missing,
            confidence_level=data.confidence_level,
            requires_fallback=requires_fallback,
        )
