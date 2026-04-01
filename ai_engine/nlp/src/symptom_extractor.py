"""
module: Extracts structured symptom data from raw transcript text.
Uses a hybrid approach:
  1. Rule-based extraction using regex + clinical keyword dictionaries
  2. LLM-based extraction 
  3. Merges results, prefers LLM where confident, falls back to rules otherwise
  
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from openai import OpenAI
load_dotenv()  # Load environment variables from .env file


from pydantic import ValidationError

from models.clinical_schema import (
    AllergyRecord,
    ClinicalFlag,
    ConfidenceLevel,
    ExtractionMethod,
    MedicalHistory,
    PatientDemographics,
    Severity,
    StructuredClinicalData,
    Symptom,
    VitalSign,
)
from src.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger("cliniq.nlp.extractor")


# Clinical keyword dictionaries (Nigerian context + paediatric focus)

SYMPTOM_KEYWORDS: Dict[str, List[str]] = {
    "fever": ["fever", "temperature", "hot body", "febrile", "high temp", "body heat"],
    "cough": ["cough", "coughing", "catarrh"],
    "difficulty_breathing": ["difficulty breathing", "shortness of breath", "breathlessness",
                              "fast breathing", "noisy breathing", "wheezing"],
    "vomiting": ["vomiting", "vomit", "throwing up", "throwing-up", "puking"],
    "diarrhoea": ["diarrhoea", "diarrhea", "loose stool", "watery stool", "running stomach"],
    "convulsion": ["convulsion", "seizure", "fitting", "shaking", "jerking"],
    "rash": ["rash", "skin rash", "spots", "redness on skin", "bumps"],
    "loss_of_appetite": ["loss of appetite", "not eating", "refusing food", "no appetite"],
    "fatigue": ["tired", "fatigue", "weakness", "lethargic", "weak"],
    "abdominal_pain": ["stomach pain", "belly pain", "abdominal pain", "tummy pain", "stomach ache"],
    "headache": ["headache", "head pain", "head ache"],
    "ear_pain": ["ear pain", "earache", "pulling ear", "ear discharge"],
    "sore_throat": ["sore throat", "throat pain", "pain swallowing"],
    "runny_nose": ["runny nose", "nasal discharge", "catarrh", "sneezing"],
    "malaria_symptoms": ["chills", "rigors", "sweating", "night sweat"],
}

SEVERITY_WORDS: Dict[Severity, List[str]] = {
    Severity.CRITICAL: ["very severe", "critical", "extremely", "worst", "can't breathe",
                         "unconscious", "not responding", "bluish"],
    Severity.HIGH: ["severe", "bad", "high", "serious", "persistent"],
    Severity.MODERATE: ["moderate", "some", "a bit", "sometimes", "on and off"],
    Severity.LOW: ["mild", "slight", "little", "minor", "small"],
}

DURATION_PATTERN = re.compile(
    r"(\d+)\s*(day|days|week|weeks|month|months|hour|hours|night|nights|morning|mornings)",
    re.IGNORECASE,
)

AGE_PATTERN = re.compile(
    r"(\d+)\s*(year|years|month|months|week|weeks)\s*old",
    re.IGNORECASE,
)

WEIGHT_PATTERN = re.compile(r"(\d+\.?\d*)\s*(kg|kilogram|kilograms)", re.IGNORECASE)
HEIGHT_PATTERN = re.compile(r"(\d+\.?\d*)\s*(cm|centimeter|centimeters|metre|meter)", re.IGNORECASE)

VITAL_PATTERNS: Dict[str, re.Pattern] = {
    "temperature": re.compile(r"temp(?:erature)?\s*(?:is|of|was|:)?\s*(\d+\.?\d*)\s*(?:degrees|°)?(?:C|F)?", re.I),
    "heart_rate": re.compile(r"(?:pulse|heart rate|HR)\s*(?:is|of|was|:)?\s*(\d+)\s*(?:bpm|per minute)?", re.I),
    "respiratory_rate": re.compile(r"(?:resp(?:iratory)? rate|RR|breathing rate)\s*(?:is|of|was|:)?\s*(\d+)", re.I),
    # "oxygen_saturation": re.compile(r"(?:spo2|oxygen sat|O2 sat|saturation)\s*(?:is|of|was|:)?\s*(\d+\.?\d*)\s*%?", re.I),
    "weight": re.compile(r"(?:weight|weighs?|wt)\s*(?:is|of|was|:)?\s*(\d+\.?\d*)\s*(kg|kilograms?)?", re.I),
}

DANGER_SIGNS = [
    ("convulsion", "Convulsion/seizure is a danger sign requiring immediate attention", Severity.CRITICAL),
    ("difficulty_breathing", "Difficulty breathing is a danger sign requiring immediate attention", Severity.CRITICAL),
    ("loss_of_consciousness", "Altered consciousness is a danger sign requiring immediate attention", Severity.CRITICAL),
    ("severe_dehydration", "Signs of severe dehydration require immediate intervention", Severity.CRITICAL),
]

# OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini"



# Rule-based extractor


class RuleBasedExtractor:
    """Fast, deterministic extraction using regex and keyword matching."""

    def extract_symptoms(self, text: str) -> List[Symptom]:
        symptoms: List[Symptom] = []
        text_lower = text.lower()

        for symptom_name, keywords in SYMPTOM_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    idx = text_lower.find(kw)
                    context = text[max(0, idx - 60): idx + 100]

                    duration = self._extract_duration(context)
                    severity = self._extract_severity(context)

                    symptoms.append(Symptom(
                        name=symptom_name,
                        raw_text=self._find_raw_phrase(text, kw),
                        duration=duration,
                        severity=severity,
                        confidence=0.75,
                    ))
                    break  # one match per symptom category

        return symptoms

    def extract_demographics(self, text: str) -> PatientDemographics:
        demographics = PatientDemographics()
        age_match = AGE_PATTERN.search(text)
        if age_match:
            demographics.age = f"{age_match.group(1)} {age_match.group(2)}"

        text_lower = text.lower()
        if any(w in text_lower for w in ["boy", "male", "his", "he ", "him "]):
            demographics.sex = "male"
        elif any(w in text_lower for w in ["girl", "female", "her ", "she ", "hers"]):
            demographics.sex = "female"

        weight_match = WEIGHT_PATTERN.search(text)
        if weight_match:
            demographics.weight_kg = float(weight_match.group(1))

        # Extract height if mentioned
        height_match = re.search(r"(?:height|tall|cm)\s*[:\s]*(\d+\.?\d*)\s*(?:cm|centimetr)", text, re.IGNORECASE)
        if height_match:
            demographics.height_cm = float(height_match.group(1))

        # Calculate BMI if both weight and height are available
        if demographics.weight_kg and demographics.height_cm:
            height_m = demographics.height_cm / 100
            demographics.bmi = demographics.weight_kg / (height_m ** 2)

        return demographics

    def extract_vitals(self, text: str) -> List[VitalSign]:
        vitals: List[VitalSign] = []
        vital_units = {
            "temperature": "°C",
            "heart_rate": "bpm",
            "respiratory_rate": "breaths/min",
            # "oxygen_saturation": "%",
            "blood_pressure": "mmHg",
        }
        vital_normal_ranges = {
            "temperature": "36.5-37.5",
            "heart_rate": "60-100",
            "respiratory_rate": "12-20",
            # "oxygen_saturation": "95-100",
            "blood_pressure": "120/80",
        }
        for vital_name, pattern in VITAL_PATTERNS.items():
            match = pattern.search(text)
            if match:
                value = match.group(1)
                is_abnormal = self._is_vital_abnormal(vital_name, float(value))
                vitals.append(VitalSign(
                    name=vital_name,
                    value=value,
                    unit=vital_units.get(vital_name),
                    normal_range=vital_normal_ranges.get(vital_name),
                    is_abnormal=is_abnormal,
                ))
        return vitals

    def extract_chief_complaint(self, text: str) -> str:
        """Extract the primary presenting complaint."""
        patterns = [
            r"(?:chief complaint|presenting complaint|reason for visit|came (?:in|to clinic) (?:for|with|because))[:\s]+(.+?)(?:\.|,|\n|$)",
            r"(?:complain(?:ing|s|t)? of|presents? with|brought in with)[:\s]+(.+?)(?:\.|,|\n|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]

        # fallback: first sentence
        sentences = re.split(r"[.!?]", text.strip())
        if sentences:
            return sentences[0].strip()[:200]
        return text[:100]

    def _extract_duration(self, context: str) -> Optional[str]:
        match = DURATION_PATTERN.search(context)
        if match:
            return match.group(0)
        return None

    def _extract_severity(self, context: str) -> Optional[Severity]:
        context_lower = context.lower()
        for severity, keywords in SEVERITY_WORDS.items():
            if any(kw in context_lower for kw in keywords):
                return severity
        return None

    def _find_raw_phrase(self, text: str, keyword: str) -> str:
        idx = text.lower().find(keyword)
        if idx == -1:
            return keyword
        return text[idx: idx + len(keyword)]

    def _is_vital_abnormal(self, vital_name: str, value: float) -> bool:
        ranges = {
            "temperature": (36.1, 37.5),
            "heart_rate": (60, 110),
            "respiratory_rate": (12, 30),
            # "oxygen_saturation": (95, 100),
            "weight": (0, 9999),  # always valid range
        }
        if vital_name in ranges:
            low, high = ranges[vital_name]
            return not (low <= value <= high)
        return False



# LLM-based extractor

class LLMExtractor:
    """Uses OpenAI API to extract structured data from transcript."""

    SYSTEM_PROMPT = """You are a clinical NLP assistant working in a Nigerian paediatric primary healthcare context.
Extract structured clinical information from the transcript provided.

IMPORTANT RULES:
- Do NOT make a diagnosis
- Do NOT suggest treatments or medications
- Extract ONLY what is explicitly mentioned in the transcript
- Return valid JSON matching the schema provided
- If information is absent, use null

Return ONLY valid JSON, no markdown, no explanation."""

    EXTRACTION_PROMPT = """Extract clinical information from this transcript and return JSON with exactly this structure:

{{
  "chief_complaint": "string",
  "symptoms": [
    {{
      "name": "normalised symptom name",
      "raw_text": "exact phrase from transcript",
      "duration": "duration string or null",
      "severity": "low|moderate|high|critical or null",
      "onset": "sudden|gradual or null",
      "location": "body location or null",
      "modifiers": ["list", "of", "descriptors"],
      "confidence": 0.0 to 1.0
    }}
  ],
  "demographics": {{
    "age": "age string or null",
    "sex": "male|female|unknown or null",
    "weight_kg": number or null
  }},
  "history": {{
    "past_conditions": [],
    "current_medications": [],
    "allergies": [],
    "immunisation_status": null
  }},
  "vital_signs": [
    {{"name": "vital name", "value": "value", "unit": "unit or null", "is_abnormal": bool}}
  ]
}}

Transcript:
{transcript}"""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.enabled = bool(self.api_key)
        if not self.enabled:
            logger.warning("OPENAI_API_KEY not set — LLM extraction disabled, using rule-based only")
        
        # Initialize official OpenAI client
        if self.enabled:
            self.client = OpenAI(api_key=self.api_key)

    def extract(self, transcript: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None

        prompt = self.EXTRACTION_PROMPT.format(transcript=transcript)

        try:
            # Using SDK instead of raw HTTP request for better error handling and retries
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            raw_text = response.choices[0].message.content.strip()

            # response = httpx.post(
            #     OPENAI_API_URL,
            #     headers={
            #         "Authorization": f"Bearer {self.api_key}",
            #         "Content-Type": "application/json",
            #     },
            #     json={
            #         "model": OPENAI_MODEL,
            #         "max_tokens": 2000,
            #         "messages": [
            #             {"role": "system", "content": self.SYSTEM_PROMPT},
            #             {"role": "user", "content": prompt}
            #         ],
            #         "temperature": 0.7,
            #     },
            #     timeout=30.0,
            # )
            # response.raise_for_status()
            # data = response.json()
            # raw_text = data["choices"][0]["message"]["content"].strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)

            return json.loads(raw_text)

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None



# Clinical flags detector

def _parse_age_to_years(age_str: Optional[str]) -> Optional[int]:
    if not age_str:
        return None
    m = re.search(r"(\d{1,3})", str(age_str))
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def detect_clinical_flags(symptoms: List[Symptom], vitals: List[VitalSign],
                          demographics: PatientDemographics, history: MedicalHistory) -> List[ClinicalFlag]:
    flags: List[ClinicalFlag] = []
    symptom_names = {s.name for s in symptoms}

    # Danger signs from symptoms
    for danger_name, description, severity in DANGER_SIGNS:
        if danger_name in symptom_names:
            flags.append(ClinicalFlag(
                flag_type="danger_sign",
                description=description,
                severity=severity,
                triggered_by=danger_name,
            ))

    # Abnormal vitals
    for vital in vitals:
        if vital.is_abnormal:
            flags.append(ClinicalFlag(
                flag_type="abnormal_vital",
                description=f"Abnormal {vital.name}: {vital.value} {vital.unit or ''}".strip(),
                severity=Severity.HIGH,
                triggered_by=vital.name,
            ))

    # Multiple high-severity symptoms
    high_severity = [s for s in symptoms if s.severity in (Severity.HIGH, Severity.CRITICAL)]
    if len(high_severity) >= 2:
        flags.append(ClinicalFlag(
            flag_type="multiple_severe_symptoms",
            description="Multiple high-severity symptoms detected — prioritise clinical review",
            severity=Severity.HIGH,
            triggered_by="symptom_pattern",
        ))

    # Composite cardiac risk: chest pain + cardiovascular risk factors
    chest_symptoms = [s for s in symptoms if "chest" in s.name or "chest" in (s.raw_text or "").lower()]
    if chest_symptoms:
        age_years = _parse_age_to_years(demographics.age)
        has_cv_risk = False
        # check past conditions for common CV risk factors
        for cond in history.past_conditions:
            if any(term in cond.lower() for term in ["hypertension", "high blood pressure", "diabetes", "diabetes mellitus", "hyperlip"]):
                has_cv_risk = True
                break
        # family history
        if not has_cv_risk and history.family_history:
            for fh in history.family_history:
                if any(term in fh.lower() for term in ["myocard", "heart attack", "stroke"]):
                    has_cv_risk = True
                    break

        if age_years and age_years >= 45:
            has_cv_risk = True

        if has_cv_risk:
            flags.append(ClinicalFlag(
                flag_type="cardiac_risk",
                description="Exertional chest pain or chest discomfort in context of cardiovascular risk factors",
                severity=Severity.HIGH,
                triggered_by=" + ".join([s.name for s in chest_symptoms]),
            ))

    return flags



# Main extractor — merges rule-based + LLM

class SymptomExtractor:
    """
    Primary entry point for extraction layer.
    Combines rule-based and LLM extraction, validates output,
    and returns a fully structured StructuredClinicalData object.
    """

    def __init__(self) -> None:
        self.rule_extractor = RuleBasedExtractor()
        self.llm_extractor = LLMExtractor()

    def extract(self, transcript: str, session_id: str,
                patient_age: Optional[str] = None,
                patient_sex: Optional[str] = None) -> Tuple[StructuredClinicalData, ExtractionMethod]:
        start = time.time()

        # Rule-based pass (always runs)
        rule_symptoms = self.rule_extractor.extract_symptoms(transcript)
        rule_demographics = self.rule_extractor.extract_demographics(transcript)
        rule_vitals = self.rule_extractor.extract_vitals(transcript)
        rule_complaint = self.rule_extractor.extract_chief_complaint(transcript)

        # Override with caller-provided demographics if given
        if patient_age:
            rule_demographics.age = patient_age
        if patient_sex:
            rule_demographics.sex = patient_sex

        # LLM pass (runs if API key present)
        llm_data = self.llm_extractor.extract(transcript)
        method = ExtractionMethod.RULE_BASED

        symptoms = rule_symptoms
        demographics = rule_demographics
        vitals = rule_vitals
        chief_complaint = rule_complaint
        history = MedicalHistory()

        if llm_data:
            method = ExtractionMethod.HYBRID
            try:
                llm_symptoms = self._parse_llm_symptoms(llm_data.get("symptoms", []))
                if llm_symptoms:
                    symptoms = self._merge_symptoms(rule_symptoms, llm_symptoms)

                llm_demo = llm_data.get("demographics", {})
                if llm_demo.get("age"):
                    demographics.age = llm_demo["age"]
                if llm_demo.get("sex"):
                    demographics.sex = llm_demo["sex"]
                if llm_demo.get("weight_kg"):
                    demographics.weight_kg = float(llm_demo["weight_kg"])
                if llm_demo.get("height_cm"):
                    demographics.height_cm = float(llm_demo["height_cm"])
                # Recalculate BMI if both weight and height available
                if demographics.weight_kg and demographics.height_cm:
                    height_m = demographics.height_cm / 100
                    demographics.bmi = demographics.weight_kg / (height_m ** 2)

                if llm_data.get("chief_complaint"):
                    chief_complaint = llm_data["chief_complaint"]

                llm_hist = llm_data.get("history", {})
                history = MedicalHistory(
                    past_conditions=llm_hist.get("past_conditions", []),
                    current_medications=llm_hist.get("current_medications", []),
                    immunisation_status=llm_hist.get("immunisation_status"),
                    family_history=llm_hist.get("family_history", []),
                    allergies=[
                        AllergyRecord(substance=a) if isinstance(a, str) else AllergyRecord(**a)
                        for a in llm_hist.get("allergies", [])
                    ],
                )

                llm_vitals = self._parse_llm_vitals(llm_data.get("vital_signs", []))
                if llm_vitals:
                    vitals = llm_vitals

            except Exception as e:
                logger.warning(f"Failed to parse LLM output, falling back to rules: {e}")
                method = ExtractionMethod.RULE_BASED

        # Clinical flags
        flags = detect_clinical_flags(symptoms, vitals, demographics, history)

        # Build result and compute confidence
        result = StructuredClinicalData(
            session_id=session_id,
            extraction_method=method,
            demographics=demographics,
            history=history,
            chief_complaint=chief_complaint,
            symptoms=symptoms,
            vital_signs=vitals,
            clinical_flags=flags,
            overall_confidence=0.0,  
            raw_transcript=transcript,
            missing_fields=[],  
        )

        # Use weighted confidence calculator
        overall_confidence = ConfidenceCalculator.compute(result)
        result.overall_confidence = overall_confidence
        result.missing_fields = self._find_missing_fields(symptoms, demographics, chief_complaint, vitals, history)
        result.extraction_warnings = self._generate_warnings(symptoms, vitals, demographics)

        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"Extraction complete in {elapsed_ms:.1f}ms | method={method.value} | "
                    f"symptoms={len(symptoms)} | confidence={overall_confidence:.2f}")

        return result, method

    # Helpers

    def _parse_llm_symptoms(self, raw: List[Dict]) -> List[Symptom]:
        symptoms = []
        for item in raw:
            try:
                symptoms.append(Symptom(
                    name=item.get("name", "unknown"),
                    raw_text=item.get("raw_text", ""),
                    duration=item.get("duration"),
                    severity=item.get("severity"),
                    onset=item.get("onset"),
                    location=item.get("location"),
                    modifiers=item.get("modifiers", []),
                    confidence=float(item.get("confidence", 0.8)),
                ))
            except (ValidationError, Exception) as e:
                logger.debug(f"Skipping malformed LLM symptom: {e}")
        return symptoms

    def _parse_llm_vitals(self, raw: List[Dict]) -> List[VitalSign]:
        vitals = []
        for item in raw:
            try:
                vitals.append(VitalSign(
                    name=item.get("name", "unknown"),
                    value=str(item.get("value", "")),
                    unit=item.get("unit"),
                    is_abnormal=bool(item.get("is_abnormal", False)),
                ))
            except Exception:
                pass
        return vitals

    def _merge_symptoms(self, rule_symptoms: List[Symptom], llm_symptoms: List[Symptom]) -> List[Symptom]:
        """Prefer LLM symptoms; add any rule-based ones not found by LLM."""
        merged = list(llm_symptoms)
        llm_names = {s.name for s in llm_symptoms}
        for rs in rule_symptoms:
            if rs.name not in llm_names:
                merged.append(rs)
        return merged

    def _compute_confidence(self, symptoms: List[Symptom], chief_complaint: str,
                             demographics: PatientDemographics) -> float:
        """Deprecated: Use ConfidenceCalculator instead."""
        score = 0.0
        weights = {"symptoms": 0.5, "chief_complaint": 0.25, "demographics": 0.25}

        if symptoms:
            avg_symptom_conf = sum(s.confidence for s in symptoms) / len(symptoms)
            score += avg_symptom_conf * weights["symptoms"]

        if chief_complaint and len(chief_complaint) > 5:
            score += weights["chief_complaint"]

        demo_score = sum([
            0.5 if demographics.age else 0,
            0.5 if demographics.sex else 0,
        ])
        score += demo_score * weights["demographics"]

        return round(min(score, 1.0), 3)

    def _find_missing_fields(self, symptoms: List[Symptom], demographics: PatientDemographics,
                              chief_complaint: str, vitals: List[VitalSign], history: MedicalHistory) -> List[str]:
        missing = []
        if not symptoms:
            missing.append("symptoms")
        if not chief_complaint:
            missing.append("chief_complaint")
        if not demographics.age:
            missing.append("patient_age")
        if not demographics.sex:
            missing.append("patient_sex")
        if not demographics.weight_kg:
            missing.append("weight_kg")
        if not demographics.height_cm:
            missing.append("height_cm")
        if not vitals:
            missing.append("vital_signs")
        if not history.past_conditions:
            missing.append("medical_history")
        if not history.current_medications:
            missing.append("current_medications")
        if not history.allergies:
            missing.append("allergies")

        # Chest-pain specific critical fields: if chest pain present, suggest ECG/troponin/smoking history
        chest_symptoms = [s for s in symptoms if "chest" in s.name or "chest" in (s.raw_text or "").lower()]
        if chest_symptoms:
            # Always request ECG and troponin results when chest pain reported
            missing.extend([f for f in ["ECG results", "Troponin levels"] if f not in missing])
            # Smoking history: check if present in past_conditions or family_history text
            smoking_known = False
            for item in (history.past_conditions or []) + (history.family_history or []):
                if isinstance(item, str) and "smok" in item.lower():
                    smoking_known = True
                    break
            if not smoking_known:
                missing.append("Smoking history")
        return missing

    def _generate_warnings(self, symptoms: List[Symptom], vitals: List[VitalSign], 
                          demographics: PatientDemographics) -> List[str]:
        """Generate warnings for missing or incomplete data."""
        warnings = []
        
        # Check for symptoms missing severity indicators
        for symptom in symptoms:
            if not symptom.severity:
                warnings.append(f"Symptom '{symptom.name}' lacks severity rating")
            if not symptom.location and symptom.name in ["pain", "ache", "discomfort"]:
                warnings.append(f"Location not specified for {symptom.name}")
        
        # Check for abnormal vitals without context
        abnormal_vitals = [v for v in vitals if v.is_abnormal]
        if len(abnormal_vitals) > 2:
            warnings.append(f"Multiple abnormal vital signs detected ({len(abnormal_vitals)})")
        
        # Check BMI status if calculable
        if demographics.weight_kg and demographics.height_cm:
            height_m = demographics.height_cm / 100
            bmi = demographics.weight_kg / (height_m ** 2)
            if bmi < 18.5:
                warnings.append("Low BMI detected (underweight range)")
            elif bmi > 30:
                warnings.append("High BMI detected (overweight/obese range)")
        
        # Chest pain specific warnings
        chest_symptoms = [s for s in symptoms if "chest" in s.name or "chest" in (s.raw_text or "").lower()]
        for s in chest_symptoms:
            raw = (s.raw_text or "").lower()
            # Radiation mention
            if not re.search(r"radiat|radiates|radiating|to the left|to the right|jaw|arm|shoulder", raw):
                warnings.append("Radiation of chest pain not mentioned")
            # Pain scale 1-10
            if not re.search(r"\b([1-9]|10)\b\s*(?:/10|out of 10)?", raw):
                warnings.append("Pain scale (1-10) not specified")
        
        return warnings




