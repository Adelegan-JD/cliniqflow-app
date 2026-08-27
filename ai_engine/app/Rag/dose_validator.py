"""
Medication dose validator.

This module performs deterministic dose safety checks using explicit
drug rules and clinical dosing formulas. It is designed to be the
authority for medication dose validation, while the RAG layer remains
an evidence/retrieval assistant only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union


class DoseSafetyLevel(str, Enum):
    """Safety category for a dose evaluation."""
    SAFE = "safe"
    CAUTION = "caution"
    UNSAFE = "unsafe"
    INSUFFICIENT_DATA = "insufficient_data"
    UNKNOWN_DRUG = "unknown_drug"


@dataclass(frozen=True)
class DrugDoseRule:
    """
    Clinical dose rule for one medication.

    - min_mgkg_per_day and max_mgkg_per_day define the safe weight-based range.
    - max_daily_mg caps the total daily dose.
    - min_age_years and max_age_years restrict the rule by age group.
    """
    name: str
    aliases: List[str]
    min_mgkg_per_day: Optional[float]
    max_mgkg_per_day: Optional[float]
    max_daily_mg: Optional[float]
    allowed_routes: Optional[List[str]] = None
    route_specific_max_single_mg: Optional[Dict[str, float]] = None
    route_specific_max_daily_mg: Optional[Dict[str, float]] = None
    max_single_dose_mg: Optional[float] = None
    min_age_years: Optional[float] = None
    max_age_years: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class DoseAssessmentResult:
    """
    Result returned by the dose validator.
    """
    drug_name: str
    normalized_drug_name: Optional[str]
    patient_age_years: Optional[float]
    patient_weight_kg: Optional[float]
    dose_mg: Optional[float]
    frequency_per_day: Optional[int]
    total_daily_mg: Optional[float]
    mgkg_per_day: Optional[float]
    safety_level: DoseSafetyLevel
    reasons: List[str]
    recommended_min_mgkg: Optional[float]
    recommended_max_mgkg: Optional[float]
    max_daily_mg: Optional[float]
    note: Optional[str] = None


# A small example medication rule registry.
# In production, this should be expanded with validated clinical references.
DRUG_RULES: Dict[str, DrugDoseRule] = {
    "amoxicillin": DrugDoseRule(
    name="amoxicillin",
    aliases=["amox", "amoxicillin trihydrate"],
    min_mgkg_per_day=20.0,
    max_mgkg_per_day=40.0,
    max_daily_mg=3000.0,
    max_single_dose_mg=1000.0,
    allowed_routes=["oral"],
    notes="Pediatric and adult weight-based dosing."
),
"ceftriaxone": DrugDoseRule(
    name="ceftriaxone",
    aliases=["rocephin"],
    min_mgkg_per_day=50.0,
    max_mgkg_per_day=100.0,
    max_daily_mg=4000.0,
    max_single_dose_mg=2000.0,
    allowed_routes=["intravenous", "intramuscular"],
    notes="Requires route-specific dosing for severe infections."
),
"paracetamol": DrugDoseRule(
    name="paracetamol",
    aliases=["acetaminophen", "tylenol"],
    min_mgkg_per_day=10.0,
    max_mgkg_per_day=15.0,
    max_daily_mg=4000.0,
    max_single_dose_mg=1000.0,
    allowed_routes=["oral"],
    notes="Standard analgesic dosing with max 4 g/day."
),
}


def _normalize_drug_name(drug_name: str) -> str:
    """Lowercase and strip medication name for registry lookup."""
    return drug_name.strip().lower()


def _find_drug_rule(drug_name: str) -> Optional[DrugDoseRule]:
    """
    Find the matching dose rule using normalized drug names and aliases.
    """
    normalized = _normalize_drug_name(drug_name)
    rule = DRUG_RULES.get(normalized)
    if rule:
        return rule

    for candidate in DRUG_RULES.values():
        if normalized in [alias.lower() for alias in candidate.aliases]:
            return candidate
    return None


def parse_age(age_string: Optional[str]) -> Optional[float]:
    """
    Parse age strings such as '5 years', '18 months', '3 months', '10'.
    Returns age in years as a float.
    """
    if not age_string:
        return None

    normalized = age_string.lower().strip()
    match = re.search(r"(\d+(\.\d+)?)", normalized)
    if not match:
        return None

    number = float(match.group(1))
    if "month" in normalized:
        return round(number / 12.0, 2)
    if "week" in normalized:
        return round(number / 52.0, 2)
    if "day" in normalized:
        return round(number / 365.0, 3)
    return number


def parse_weight(weight_kg: Optional[float]) -> Optional[float]:
    """
    Accept a weight in kilograms. In a production system, this may be extended
    to parse pounds or other units if necessary.
    """
    if weight_kg is None or weight_kg <= 0:
        return None
    return float(weight_kg)

def _normalize_route(route: Optional[str]) -> Optional[str]:
    if not route:
        return None
    return route.strip().lower().replace(" ", "_")

def parse_age(age_input: Optional[Union[str, float, int]]) -> Optional[float]:
    if age_input is None:
        return None
    if isinstance(age_input, (int, float)):
        return float(age_input) if age_input >= 0 else None
    normalized = str(age_input).lower()
    match = re.search(r"(\d+(?:\.\d+)?)", normalized)
    if not match:
        return None
    value = float(match.group(1))
    if "month" in normalized or "mo" in normalized:
        return round(value / 12.0, 2)
    if "week" in normalized or "wk" in normalized:
        return round(value / 52.0, 2)
    if "day" in normalized or "d" in normalized:
        return round(value / 365.0, 3)
    return value

def parse_weight(weight_input: Optional[Union[str, float, int]]) -> Optional[float]:
    if weight_input is None:
        return None
    if isinstance(weight_input, (int, float)):
        return float(weight_input) if weight_input > 0 else None
    normalized = str(weight_input).lower()
    match = re.search(r"(\d+(?:\.\d+)?)", normalized)
    if not match:
        return None
    value = float(match.group(1))
    if "lb" in normalized or "pound" in normalized:
        return round(value * 0.45359237, 2)
    return round(value, 2)

def parse_dose(dose_input: Optional[Union[str, float, int]]) -> Optional[float]:
    if dose_input is None:
        return None
    if isinstance(dose_input, (int, float)):
        return float(dose_input) if dose_input >= 0 else None
    normalized = str(dose_input).lower()
    match = re.search(r"(\d+(?:\.\d+)?)", normalized)
    if not match:
        return None
    value = float(match.group(1))
    if "g" in normalized and "mg" not in normalized:
        return round(value * 1000.0, 2)
    return round(value, 2)

def parse_frequency(frequency_input: Optional[Union[str, int]]) -> Optional[int]:
    if frequency_input is None:
        return None
    if isinstance(frequency_input, int):
        return frequency_input if frequency_input > 0 else None
    normalized = str(frequency_input).lower()
    freq_map = {
        "once": 1,
        "daily": 1,
        "qd": 1,
        "bid": 2,
        "twice daily": 2,
        "tid": 3,
        "t.i.d": 3,
        "three times daily": 3,
        "q8h": 3,
        "q12h": 2,
        "q6h": 4,
        "q4h": 6,
        "q24h": 1,
    }
    if normalized in freq_map:
        return freq_map[normalized]
    match = re.search(r"(\d+)", normalized)
    if match:
        value = int(match.group(1))
        return value if value > 0 else None
    return None


def calculate_mgkg_per_day(
    dose_mg: float,
    frequency_per_day: int,
    weight_kg: float,
) -> Optional[float]:
    """
    Convert a dose and frequency into mg per kg per day.
    """
    if dose_mg is None or frequency_per_day is None or weight_kg is None:
        return None
    total_daily = dose_mg * frequency_per_day
    if weight_kg <= 0:
        return None
    return round(total_daily / weight_kg, 3)


def _check_age_rule(rule: DrugDoseRule, age_years: Optional[float], reasons: List[str]) -> None:
    """
    Add warnings if the patient age is outside the rule boundary.
    """
    if age_years is None:
        reasons.append("Patient age is missing; age-specific rule boundaries cannot be verified.")
        return

    if rule.min_age_years is not None and age_years < rule.min_age_years:
        reasons.append(
            f"Patient age {age_years:.2f} years is below the supported minimum of "
            f"{rule.min_age_years} years for {rule.name}."
        )
    if rule.max_age_years is not None and age_years > rule.max_age_years:
        reasons.append(
            f"Patient age {age_years:.2f} years is above the supported maximum of "
            f"{rule.max_age_years} years for {rule.name}."
        )

def _route_check(
    rule: DrugDoseRule,
    route: Optional[str],
    dose_mg: Optional[float],
    total_daily_mg: Optional[float],
    reasons: List[str],
) -> None:
    if route is None:
        return
    route_key = _normalize_route(route)

    if rule.allowed_routes and route_key not in rule.allowed_routes:
        reasons.append(
            f"Route '{route}' is not expected for {rule.name}; confirm if this route is appropriate."
        )

    if rule.route_specific_max_single_mg and route_key in rule.route_specific_max_single_mg and dose_mg is not None:
        route_max = rule.route_specific_max_single_mg[route_key]
        if dose_mg > route_max:
            reasons.append(
                f"Single dose {dose_mg:.1f} mg exceeds the route-specific maximum of "
                f"{route_max:.1f} mg for {route}."
            )

    if rule.route_specific_max_daily_mg and route_key in rule.route_specific_max_daily_mg and total_daily_mg is not None:
        route_max_daily = rule.route_specific_max_daily_mg[route_key]
        if total_daily_mg > route_max_daily:
            reasons.append(
                f"Total daily dose {total_daily_mg:.1f} mg exceeds the route-specific maximum of "
                f"{route_max_daily:.1f} mg for {route}."
            )

def assess_dose(
    drug_name: str,
    dose_mg: Optional[float],
    frequency_per_day: Optional[int],
    patient_weight_kg: Optional[float],
    patient_age_years: Optional[float],
    route: Optional[str] = None,
) -> DoseAssessmentResult:
    """
    Evaluate a medication dose and return a detailed safety assessment.
    """
    normalized_drug_name = _normalize_drug_name(drug_name)
    rule = _find_drug_rule(drug_name)

    total_daily_mg: Optional[float] = None
    mgkg_per_day: Optional[float] = None
    reasons: List[str] = []

    if dose_mg is not None and frequency_per_day is not None:
        total_daily_mg = dose_mg * frequency_per_day

    if total_daily_mg is not None and patient_weight_kg is not None:
        mgkg_per_day = calculate_mgkg_per_day(dose_mg, frequency_per_day, patient_weight_kg)

    if rule is None:
        return DoseAssessmentResult(
            drug_name=drug_name,
            normalized_drug_name=None,
            patient_age_years=patient_age_years,
            patient_weight_kg=patient_weight_kg,
            dose_mg=dose_mg,
            frequency_per_day=frequency_per_day,
            total_daily_mg=total_daily_mg,
            mgkg_per_day=mgkg_per_day,
            safety_level=DoseSafetyLevel.UNKNOWN_DRUG,
            reasons=["Drug is not present in the dose rule registry."],
            recommended_min_mgkg=None,
            recommended_max_mgkg=None,
            max_daily_mg=None,
            note="Add this drug to the DRUG_RULES registry before using it in production."
        )

    if dose_mg is None:
        reasons.append("Dose amount is missing.")
    if frequency_per_day is None:
        reasons.append("Dose frequency is missing.")
    if patient_weight_kg is None and rule.min_mgkg_per_day is not None:
        reasons.append("Patient weight is missing; weight-based dose validation is not possible.")
    if patient_age_years is None and (rule.min_age_years or rule.max_age_years):
        reasons.append("Patient age is missing; age-specific rule boundaries cannot be verified.")

    _check_age_rule(rule, patient_age_years, reasons)
    _route_check(rule, route, dose_mg, total_daily_mg, reasons)

    if total_daily_mg is None:
        return DoseAssessmentResult(
            drug_name=drug_name,
            normalized_drug_name=rule.name,
            patient_age_years=patient_age_years,
            patient_weight_kg=patient_weight_kg,
            dose_mg=dose_mg,
            frequency_per_day=frequency_per_day,
            total_daily_mg=total_daily_mg,
            mgkg_per_day=mgkg_per_day,
            safety_level=DoseSafetyLevel.INSUFFICIENT_DATA,
            reasons=reasons or ["Insufficient data to compute the dose."],
            recommended_min_mgkg=rule.min_mgkg_per_day,
            recommended_max_mgkg=rule.max_mgkg_per_day,
            max_daily_mg=rule.max_daily_mg,
            note="Provide both dose and frequency to evaluate daily medication exposure."
        )

    if rule.max_daily_mg is not None and total_daily_mg > rule.max_daily_mg:
        reasons.append(
            f"Total daily dose {total_daily_mg:.1f} mg exceeds the maximum allowed "
            f"{rule.max_daily_mg:.1f} mg for {rule.name}."
        )

    if rule.max_single_dose_mg is not None and dose_mg is not None and dose_mg > rule.max_single_dose_mg:
        reasons.append(
            f"Single dose {dose_mg:.1f} mg exceeds the maximum single dose "
            f"{rule.max_single_dose_mg:.1f} mg for {rule.name}."
        )

    if rule.min_mgkg_per_day is not None and mgkg_per_day is not None:
        if mgkg_per_day < rule.min_mgkg_per_day:
            reasons.append(
                f"Calculated dose {mgkg_per_day:.2f} mg/kg/day is below the minimum "
                f"{rule.min_mgkg_per_day:.2f} mg/kg/day."
            )
        if mgkg_per_day > rule.max_mgkg_per_day:
            reasons.append(
                f"Calculated dose {mgkg_per_day:.2f} mg/kg/day exceeds the maximum "
                f"{rule.max_mgkg_per_day:.2f} mg/kg/day."
            )

    if rule.max_daily_mg is not None and total_daily_mg is not None and total_daily_mg <= rule.max_daily_mg:
        if rule.min_mgkg_per_day is None or mgkg_per_day is None:
            # if we can't do mg/kg, still allow adult max-check safe path
            if not reasons:
                return DoseAssessmentResult(
                    drug_name=drug_name,
                    normalized_drug_name=rule.name,
                    patient_age_years=patient_age_years,
                    patient_weight_kg=patient_weight_kg,
                    dose_mg=dose_mg,
                    frequency_per_day=frequency_per_day,
                    total_daily_mg=total_daily_mg,
                    mgkg_per_day=mgkg_per_day,
                    safety_level=DoseSafetyLevel.SAFE,
                    reasons=["Dose is within the maximum daily limit."],
                    recommended_min_mgkg=rule.min_mgkg_per_day,
                    recommended_max_mgkg=rule.max_mgkg_per_day,
                    max_daily_mg=rule.max_daily_mg,
                )

    if reasons:
        level = DoseSafetyLevel.UNSAFE if any("exceeds" in msg for msg in reasons) else DoseSafetyLevel.CAUTION
    else:
        level = DoseSafetyLevel.SAFE

    return DoseAssessmentResult(
        drug_name=drug_name,
        normalized_drug_name=rule.name,
        patient_age_years=patient_age_years,
        patient_weight_kg=patient_weight_kg,
        dose_mg=dose_mg,
        frequency_per_day=frequency_per_day,
        total_daily_mg=total_daily_mg,
        mgkg_per_day=mgkg_per_day,
        safety_level=level,
        reasons=reasons or ["Dose is within the defined safe range."],
        recommended_min_mgkg=rule.min_mgkg_per_day,
        recommended_max_mgkg=rule.max_mgkg_per_day,
        max_daily_mg=rule.max_daily_mg,
        note=rule.notes,
    )


if __name__ == "__main__":
    # Example usage for local testing
    age = parse_age("5 years")
    weight = parse_weight(18.0)
    result = assess_dose(
        drug_name="Amoxicillin",
        dose_mg=200.0,
        frequency_per_day=3,
        patient_weight_kg=weight,
        patient_age_years=age,
        route="oral,"
    )

    print("Safety level:", result.safety_level)
    print("Total daily mg:", result.total_daily_mg)
    print("mg/kg/day:", result.mgkg_per_day)
    print("Reasons:")
    for reason in result.reasons:
        print("-", reason)
