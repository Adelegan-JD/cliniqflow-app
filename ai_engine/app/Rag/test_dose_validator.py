import pytest
from ai_engine.app.rag.dose_validator import (
    DoseSafetyLevel,
    assess_dose,
    parse_age,
    parse_weight,
    parse_dose,
    parse_frequency,
)

def test_safe_amoxicillin_oral():
    result = assess_dose(
        drug_name="Amoxicillin",
        dose_mg=200.0,
        frequency_per_day=3,
        patient_weight_kg=18.0,
        patient_age_years=5.0,
        route="oral",
    )
    assert result.safety_level == DoseSafetyLevel.SAFE
    assert "Dose is within" in result.reasons[0] or result.reasons

def test_unsafe_paracetamol_above_daily_max():
    result = assess_dose(
        drug_name="Paracetamol",
        dose_mg=1000.0,
        frequency_per_day=5,
        patient_weight_kg=70.0,
        patient_age_years=30.0,
        route="oral",
    )
    assert result.safety_level == DoseSafetyLevel.UNSAFE
    assert any("exceeds the maximum allowed" in r for r in result.reasons)

def test_unknown_drug_returns_unknown_drug():
    result = assess_dose(
        drug_name="UnknownDrug",
        dose_mg=100.0,
        frequency_per_day=1,
        patient_weight_kg=60.0,
        patient_age_years=25.0,
    )
    assert result.safety_level == DoseSafetyLevel.UNKNOWN_DRUG

def test_insufficient_data_missing_frequency():
    result = assess_dose(
        drug_name="Amoxicillin",
        dose_mg=250.0,
        frequency_per_day=None,
        patient_weight_kg=18.0,
        patient_age_years=5.0,
    )
    assert result.safety_level == DoseSafetyLevel.INSUFFICIENT_DATA
    assert any("missing" in r.lower() for r in result.reasons)

def test_route_validation_rejects_oral_ceftriaxone():
    result = assess_dose(
        drug_name="Ceftriaxone",
        dose_mg=500.0,
        frequency_per_day=1,
        patient_weight_kg=40.0,
        patient_age_years=10.0,
        route="oral",
    )
    assert result.safety_level == DoseSafetyLevel.CAUTION
    assert any("not expected for ceftriaxone" in r.lower() for r in result.reasons)

def test_parsers_convert_units():
    assert parse_dose("1 g") == 1000.0
    assert parse_weight("154 lbs") == pytest.approx(69.85, rel=1e-3)
    assert parse_age("18 months") == pytest.approx(1.5)
    assert parse_frequency("three times daily") == 3