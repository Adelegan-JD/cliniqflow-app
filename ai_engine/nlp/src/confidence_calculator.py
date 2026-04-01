"""
module: Computes overall extraction confidence from individual component scores.
Uses weighted average of symptom, vital, demographic, and history extractions.

"""

from __future__ import annotations

from typing import List

from models.clinical_schema import (
    StructuredClinicalData,
    Symptom,
    VitalSign,
)


class ConfidenceCalculator:
    """
    Computes aggregate confidence score for extraction.
    Weights:
    - Symptoms: 40% (most clinically relevant)
    - Vitals: 30% (objective, high impact)
    - Demographics: 15% (support only)
    - History: 15% (lower priority)
    """

    WEIGHTS = {
        "symptoms": 0.40,
        "vitals": 0.30,
        "demographics": 0.15,
        "history": 0.15,
    }

    @classmethod
    def compute(cls, data: StructuredClinicalData) -> float:
        """
        Compute overall confidence 0-1 based on component extractions.
        """
        scores: dict[str, float] = {}

        # Symptom confidence
        scores["symptoms"] = cls._symptom_confidence(data.symptoms)

        # Vital sign confidence (all vitals are binary: present or not)
        scores["vitals"] = cls._vital_confidence(data.vital_signs)

        # Demographics confidence
        scores["demographics"] = cls._demographic_confidence(data)

        # History confidence
        scores["history"] = cls._history_confidence(data)

        # Weighted aggregate
        total = sum(
            scores.get(key, 0.0) * weight
            for key, weight in cls.WEIGHTS.items()
        )
        return round(total, 3)

    @staticmethod
    def _symptom_confidence(symptoms: List[Symptom]) -> float:
        """Average confidence of extracted symptoms."""
        if not symptoms:
            return 0.0
        return sum(s.confidence for s in symptoms) / len(symptoms)

    @staticmethod
    def _vital_confidence(vitals: List[VitalSign]) -> float:
        """
        Vitals presence score.
        Each vital found increases confidence; assume 0.90 per vital.
        Max 1.0 with 2+ vitals.
        """
        if not vitals:
            return 0.0
        return min(1.0, len(vitals) * 0.50)

    @staticmethod
    def _demographic_confidence(data: StructuredClinicalData) -> float:
        """Demographics presence score."""
        score = 0.0
        total_fields = 0

        d = data.demographics
        fields = [d.age, d.sex, d.weight_kg, d.height_cm, d.bmi]
        present = sum(1 for f in fields if f is not None)
        total_fields = len(fields)

        if total_fields > 0:
            score = present / total_fields
        return score

    @staticmethod
    def _history_confidence(data: StructuredClinicalData) -> float:
        """Medical history presence score."""
        score = 0.0
        total_items = 0

        h = data.history
        items = [
            h.past_conditions,
            h.current_medications,
            h.allergies,
            h.family_history,
            h.immunisation_status,
        ]
        for item in items:
            if isinstance(item, list):
                total_items += 1
                if item:
                    score += 1.0
            elif item:
                total_items += 1
                score += 1.0

        if total_items > 0:
            score = score / total_items
        return score
