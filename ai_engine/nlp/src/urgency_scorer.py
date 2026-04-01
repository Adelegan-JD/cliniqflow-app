"""
Computes urgency level from vital signs only.

Flow:
Nurse enters vitals (temp, HR, RR, weight, height, SpO2) →
urgency_scorer computes level →
Nurse sees urgency badge (Red/Yellow/Green) →
Doctor reviews full assessment


Universal triage scoring module (0-100+ years).

Vitals Supported:
- Temperature
- Heart Rate
- Respiratory Rate
- Blood Pressure (systolic/diastolic)
- Oxygen Saturation (SpO₂) (optional)
- Weight (optional for BMI)
- Height (optional for BMI)

Outputs:
- EMERGENCY (Red)
- URGANT (Yellow)
- NORMAL (Green)
"""
# from __future__ import annotations
# from enum import Enum
# from typing import List, Optional
 
# from models.clinical_schema import PatientDemographics, VitalSign
 
 
# # URGENCY LEVELS
 
# class UrgencyLevel(str, Enum):
#     EMERGENCY = "emergency"
#     URGENT = "urgent"
#     NORMAL = "normal"
 
 
# class UrgencyScore:
#     def __init__(
#         self,
#         level: UrgencyLevel,
#         score: int,
#         reasons: List[str],
#         abnormal_vitals: List[str],
#     ):
#         self.level = level
#         self.score = score
#         self.reasons = reasons
#         self.abnormal_vitals = abnormal_vitals
 
#     def to_dict(self):
#         return {
#             "level": self.level.value,
#             "score": self.score,
#             "reasons": self.reasons,
#             "abnormal_vitals": self.abnormal_vitals,
#         }
 
 
# # URGENCY SCORER
 
# class UrgencyScorer:
 
#     VITAL_RANGES = {
#         "temperature": {
#             "critical_low": 35.0,
#             "low": 36.0,
#             "normal": (36.5, 37.5),
#             "high": 38.0,
#             "critical_high": 40.0,
#         },
#         "heart_rate": {
#             "adult": {"critical_low": 40, "low": 50, "normal": (60, 100), "high": 120, "critical_high": 150},
#         },
#         "respiratory_rate": {
#             "adult": {"critical_low": 8, "low": 10, "normal": (12, 20), "high": 25, "critical_high": 35},
#         },
#         "blood_pressure": {
#             "critical_low_sys": 70,
#             "low_sys": 90,
#             "normal": (100, 130),  # Changed from normal_sys to normal
#             "high_sys": 150,
#             "critical_high_sys": 180,
#         },
#         "oxygen_saturation": {
#             "critical_low": 85,
#             "low": 90,
#             "normal": (95, 100),
#         },
#     }
 
#     def score(self, vitals: List[VitalSign], demographics: PatientDemographics) -> UrgencyScore:
 
#         score = 0
#         reasons = []
#         abnormal_vitals = []
 
#         systolic = None
#         diastolic = None
 
#         # Check each vital
#         for vital in vitals:
#             name = vital.name.lower()
#             try:
#                 value = float(vital.value)
#             except (ValueError, TypeError):
#                 continue
 
#             if "temp" in name:
#                 severity = self._assess_temperature(value)
#             elif "heart" in name or "pulse" in name:
#                 severity = self._assess_heart_rate(value)
#             elif "resp" in name or "breath" in name:
#                 severity = self._assess_respiratory_rate(value)
#             elif "oxygen" in name or "spo2" in name:
#                 severity = self._assess_oxygen_saturation(value)
#             elif "blood" in name or "pressure" in name:
#                 try:
#                     parts = str(vital.value).split("/")
#                     systolic = float(parts[0])
#                     diastolic = float(parts[1])
#                     continue
#                 except (ValueError, IndexError):
#                     continue
#             else:
#                 continue
 
#             score, reasons, abnormal_vitals = self._update_score(
#                 severity, score, vital, reasons, abnormal_vitals
#             )
 
#         # Blood pressure check
#         if systolic is not None:
#             severity = self._assess_blood_pressure(systolic)
#             if severity != "normal":
#                 bp_vital = VitalSign(name="Blood Pressure", value=f"{systolic}/{diastolic}", unit="mmHg")
#                 score, reasons, abnormal_vitals = self._update_score(
#                     severity, score, bp_vital, reasons, abnormal_vitals
#                 )
 
#         # BMI / Extreme Weight check
#         if demographics.weight_kg:
#             if demographics.height_cm:
#                 bmi = demographics.weight_kg / ((demographics.height_cm / 100) ** 2)
#                 if bmi < 16 or bmi > 35:
#                     score = max(score, 50)
#                     reasons.append(f"Abnormal BMI: {bmi:.1f}")
#             else:
#                 if demographics.weight_kg < 30 or demographics.weight_kg > 200:
#                     score = max(score, 40)
#                     reasons.append("Extreme body weight detected")
 
#         # Classification 
#         if score >= 80:
#             level = UrgencyLevel.EMERGENCY
#         elif score >= 40:
#             level = UrgencyLevel.URGENT
#         else:
#             level = UrgencyLevel.NORMAL
 
#         return UrgencyScore(level, score, reasons, abnormal_vitals)
 
 
#     # Assessment Helpers
 
#     def _assess_temperature(self, value: float) -> str:
#         r = self.VITAL_RANGES["temperature"]
#         if value < r["critical_low"] or value > r["critical_high"]:
#             return "critical"
#         elif value < r["low"] or value > r["high"]:
#             return "high"
#         return "normal"
 
#     def _assess_heart_rate(self, value: float) -> str:
#         r = self.VITAL_RANGES["heart_rate"]["adult"]
#         if value < r["critical_low"] or value > r["critical_high"]:
#             return "critical"
#         elif value < r["low"] or value > r["high"]:
#             return "high"
#         return "normal"
 
#     def _assess_respiratory_rate(self, value: float) -> str:
#         r = self.VITAL_RANGES["respiratory_rate"]["adult"]
#         if value < r["critical_low"] or value > r["critical_high"]:
#             return "critical"
#         elif value < r["low"] or value > r["high"]:
#             return "high"
#         return "normal"
 
#     def _assess_blood_pressure(self, systolic: float) -> str:
#         r = self.VITAL_RANGES["blood_pressure"]
#         if systolic < r["critical_low_sys"] or systolic > r["critical_high_sys"]:
#             return "critical"
#         elif systolic < r["low_sys"] or systolic > r["high_sys"]:
#             return "high"
#         return "normal"
 
#     def _assess_oxygen_saturation(self, value: float) -> str:
#         r = self.VITAL_RANGES["oxygen_saturation"]
#         if value < r["critical_low"]:
#             return "critical"
#         elif value < r["low"]:
#             return "high"
#         return "normal"

#     def _update_score(self, severity: str, score: int, vital: VitalSign, reasons: List[str], abnormal_vitals: List[str]):
#         if severity == "critical":
#             score = max(score, 90)
#             reasons.append(f"CRITICAL: {vital.name} = {vital.value}")
#             abnormal_vitals.append(vital.name)
#         elif severity == "high":
#             score = max(score, 50)
#             reasons.append(f"Abnormal: {vital.name} = {vital.value}")
#             abnormal_vitals.append(vital.name)
#         return score, reasons, abnormal_vitals
 
 
# def score_urgency(vitals, demographics):
#     """Wrapper used by orchestration pipeline."""
#     scorer = UrgencyScorer()
#     result = scorer.score(vitals, demographics)
#     return result.to_dict()





from __future__ import annotations
from enum import Enum
from typing import List, Optional
import re  # ✅ NEW: for parsing age strings

from models.clinical_schema import PatientDemographics, VitalSign


# URGENCY LEVELS

class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    NORMAL = "normal"


class UrgencyScore:
    def __init__(
        self,
        level: UrgencyLevel,
        score: int,
        reasons: List[str],
        abnormal_vitals: List[str],
    ):
        self.level = level
        self.score = score
        self.reasons = reasons
        self.abnormal_vitals = abnormal_vitals

    def to_dict(self):
        return {
            "level": self.level.value,
            "score": self.score,
            "reasons": self.reasons,
            "abnormal_vitals": self.abnormal_vitals,
        }


# URGENCY SCORER

class UrgencyScorer:

    VITAL_RANGES = {
        "temperature": {
            "critical_low": 35.0,
            "low": 36.0,
            "normal": (36.5, 37.5),
            "high": 38.0,
            "critical_high": 40.0,
        },
        "heart_rate": {
            # ✅ NEW: AGE-BASED RANGES
            "newborn": (100, 180),
            "infant": (100, 160),
            "child": (70, 120),
            "adult": (60, 100),
            "elderly": (55, 95),
        },
        "respiratory_rate": {
            # ✅ NEW: AGE-BASED RANGES
            "newborn": (30, 60),
            "infant": (30, 50),
            "child": (20, 30),
            "adult": (12, 20),
            "elderly": (12, 22),
        },
        "blood_pressure": {
            "critical_low_sys": 70,
            "low_sys": 90,
            "normal": (100, 130),
            "high_sys": 150,
            "critical_high_sys": 180,
        },
        "oxygen_saturation": {
            "critical_low": 85,
            "low": 90,
            "normal": (95, 100),
        },
    }

    # =========================
    # ✅ NEW: AGE HANDLING
    # =========================

    def _parse_age(self, age_str: str) -> float:
        """Convert '5 years', '3 months', '2 days' → years"""
        if not age_str:
            return 0

        age_str = age_str.lower()

        number = float(re.findall(r"\d+\.?\d*", age_str)[0]) if re.findall(r"\d+\.?\d*", age_str) else 0

        if "day" in age_str:
            return number / 365
        elif "month" in age_str:
            return number / 12
        return number  # assume years

    def _normalize_age(self, age: float) -> float:
        """Clamp age between 0 and 130"""
        if age < 0:
            return 0
        if age > 130:
            return 130
        return age

    def _get_age_group(self, age: float) -> str:
        """Map age → physiological group"""
        if age < 0.08:
            return "newborn"
        elif age < 1:
            return "infant"
        elif age < 18:
            return "child"
        elif age < 65:
            return "adult"
        else:
            return "elderly"

    # =========================
    # MAIN SCORING
    # =========================

    def score(self, vitals: List[VitalSign], demographics: PatientDemographics) -> UrgencyScore:

        score = 0
        reasons = []
        abnormal_vitals = []

        systolic = None
        diastolic = None

        # ✅ NEW: AGE PROCESSING
        age_years = self._parse_age(demographics.age)
        age_years = self._normalize_age(age_years)
        age_group = self._get_age_group(age_years)

        # Check each vital
        for vital in vitals:
            name = vital.name.lower()

            try:
                value = float(vital.value)
            except (ValueError, TypeError):
                continue

            if "temp" in name:
                severity = self._assess_temperature(value, age_group)  # ✅ UPDATED
            elif "heart" in name or "pulse" in name:
                severity = self._assess_heart_rate(value, age_group)  # ✅ UPDATED
            elif "resp" in name or "breath" in name:
                severity = self._assess_respiratory_rate(value, age_group)  # ✅ UPDATED
            elif "oxygen" in name or "spo2" in name:
                severity = self._assess_oxygen_saturation(value)
            elif "blood" in name or "pressure" in name:
                try:
                    parts = str(vital.value).split("/")
                    systolic = float(parts[0])
                    diastolic = float(parts[1])
                    continue
                except:
                    continue
            else:
                continue

            score, reasons, abnormal_vitals = self._update_score(
                severity, score, vital, reasons, abnormal_vitals
            )

        # Blood pressure check
        if systolic is not None:
            severity = self._assess_blood_pressure(systolic)
            score, reasons, abnormal_vitals = self._update_score(
                severity, score,
                VitalSign(name="Blood Pressure", value=f"{systolic}/{diastolic}", unit="mmHg"),
                reasons, abnormal_vitals
            )

        # BMI / Extreme Weight
        if demographics.weight_kg:
            if demographics.height_cm:
                bmi = demographics.weight_kg / ((demographics.height_cm / 100) ** 2)
                if bmi < 16 or bmi > 35:
                    score = max(score, 50)
                    reasons.append(f"Abnormal BMI: {bmi:.1f}")
            else:
                if demographics.weight_kg < 30 or demographics.weight_kg > 200:
                    score = max(score, 40)
                    reasons.append("Extreme body weight detected")

        # ✅ NEW: ELDERLY SENSITIVITY BOOST
        if age_group == "elderly" and abnormal_vitals:
            score += 10
            reasons.append("Elderly risk adjustment applied")

        # Classification
        if score >= 80:
            level = UrgencyLevel.EMERGENCY
        elif score >= 40:
            level = UrgencyLevel.URGENT
        else:
            level = UrgencyLevel.NORMAL

        return UrgencyScore(level, score, reasons, abnormal_vitals)

    # =========================
    # UPDATED ASSESSORS
    # =========================

    def _assess_temperature(self, value: float, age_group: str) -> str:
        r = self.VITAL_RANGES["temperature"]

        # ✅ Elderly more sensitive to fever
        if age_group == "elderly" and value >= 37.5:
            return "high"

        if value < r["critical_low"] or value > r["critical_high"]:
            return "critical"
        elif value < r["low"] or value > r["high"]:
            return "high"
        return "normal"

    def _assess_heart_rate(self, value: float, age_group: str) -> str:
        low, high = self.VITAL_RANGES["heart_rate"][age_group]

        if value < low * 0.7 or value > high * 1.5:
            return "critical"
        elif value < low or value > high:
            return "high"
        return "normal"

    def _assess_respiratory_rate(self, value: float, age_group: str) -> str:
        low, high = self.VITAL_RANGES["respiratory_rate"][age_group]

        if value < low * 0.7 or value > high * 1.5:
            return "critical"
        elif value < low or value > high:
            return "high"
        return "normal"

    def _assess_blood_pressure(self, systolic: float) -> str:
        r = self.VITAL_RANGES["blood_pressure"]

        if systolic < r["critical_low_sys"] or systolic > r["critical_high_sys"]:
            return "critical"
        elif systolic < r["low_sys"] or systolic > r["high_sys"]:
            return "high"
        return "normal"

    def _assess_oxygen_saturation(self, value: float) -> str:
        r = self.VITAL_RANGES["oxygen_saturation"]

        if value < r["critical_low"]:
            return "critical"
        elif value < r["low"]:
            return "high"
        return "normal"

    def _update_score(self, severity: str, score: int, vital: VitalSign, reasons: List[str], abnormal_vitals: List[str]):
        if severity == "critical":
            score = max(score, 90)
            reasons.append(f"CRITICAL: {vital.name} = {vital.value}")
            abnormal_vitals.append(vital.name)
        elif severity == "high":
            score = max(score, 50)
            reasons.append(f"Abnormal: {vital.name} = {vital.value}")
            abnormal_vitals.append(vital.name)

        return score, reasons, abnormal_vitals


def score_urgency(vitals, demographics):
    scorer = UrgencyScorer()
    return scorer.score(vitals, demographics).to_dict()