# CliniqFlow - System Enhancements & Data Model Documentation

## Overview

CliniqFlow has been enhanced with professional-grade clinical data handling capabilities. These enhancements make the system suitable for healthcare settings serving patients of all ages and demographics.

## Summary of Enhancements

This document describes the advanced data structures and processing capabilities that were added to improve clinical accuracy, data integrity, and professional medical documentation standards.

### 1. **Enhanced Demographics Tracking**

**What Changed:**
- Added `height_cm` field to capture patient height
- Implemented automatic BMI (Body Mass Index) calculation
- BMI is computed from weight and height and stored with each extraction

**Why It Matters:**
- Height is critical for pediatric assessment (growth tracking)
- BMI calculation helps identify nutrition-related concerns
- Important for medication dosing calculations

**Usage Example:**
```python
demographics = PatientDemographics(
    age="45 years",
    sex="male",
    weight_kg=88,
    height_cm=172  # New field
    # BMI is automatically calculated: 29.74
)
```

---

### 2. **Enhanced Vital Signs Model**

**Fields Added:**
- `unit` - Unit of measurement (e.g., "mmHg", "°C", "bpm")
- `normal_range` - Expected normal value for clinical context
- `is_abnormal` - Boolean flag for quick abnormality detection
- `severity` - Classification of abnormality

**Why It Matters:**
- Different units are used in different regions/countries
- Displaying normal ranges gives clinical context
- Automatic abnormality flagging for urgent assessment

**Usage Example:**
```python
vital_sign = VitalSign(
    name="Blood Pressure",
    value="155/98",
    unit="mmHg",                    # New
    normal_range="120/80",           # New
    is_abnormal=True,                # New
    severity="high"
)
```

---

### 3. **Improved Medical History**

**What Changed:**
- Added `family_history` field to capture familial medical conditions
- Now captures full medical context including genetic risk factors

**Why It Matters:**
- Family history is critical for risk stratification
- Many conditions have hereditary components (hypertension, diabetes, cancer)
- Essential for preventive health planning

**Usage Example:**
```python
medical_history = MedicalHistory(
    past_medical_conditions=["hypertension", "type_2_diabetes"],
    current_medications=["metformin", "lisinopril"],
    allergies=["penicillin"],
    family_history=[                 # New
        "Father: myocardial infarction at age 60",
        "Mother: type 2 diabetes",
        "Sibling: asthma"
    ]
)
```

---

### 4. **Better Symptom Extraction**

**Fields Added:**
- `location` - Where the symptom is felt (e.g., "left chest", "lower abdomen")
- `modifiers` - Descriptive context (e.g., "worse with exertion", "improves with rest")
- `onset` - Descriptive onset information (e.g., "sudden", "gradual", "3 days ago")

**Why It Matters:**
- Location helps pinpoint clinical problems
- Modifiers provide clinical context for diagnosis
- Onset patterns help distinguish different etiologies

**Usage Example:**
```python
symptom = Symptom(
    name="chest pain",
    severity="high",
    location="left anterior chest",   # New
    onset="sudden",                    # New
    modifiers=["worse with exertion"] # New
)
```

---

### 5. **Comprehensive Confidence Scoring**

**New Module: `ConfidenceCalculator`**

**Scoring Approach:**
Uses weighted scoring across clinical components:

```python
COMPONENT_WEIGHTS = {
    "symptoms": 0.40,           # 40% - Most clinically relevant
    "vitals": 0.30,             # 30% - Objective, high impact
    "demographics": 0.15,       # 15% - Basic info
    "medical_history": 0.15,    # 15% - Background context
}
```

**Calculation Formula:**
```
Confidence = (Σ component_confidence × weight) / 100
Range: 0 (not confident) to 1 (very confident)
```

**Classification:**
```
HIGH   = 0.85 - 1.00  (Reliable for clinical use)
MEDIUM = 0.60 - 0.84  (Probably accurate, review recommended)
LOW    = 0.00 - 0.59  (Use with caution, incomplete data)
```

**Why It Matters:**
- Provides transparency to end users
- Helps clinicians decide whether data is reliable
- Flags when additional information is needed
- Improves clinical decision-making safety

---

### 6. **Enhanced Data Quality Metrics**

**New Outputs:**

#### **Missing Fields Detection**
Lists critical missing data:
```python
{
    "missing_fields": [
        "smoking_history",
        "respiratory_rate",
        "medication_list",
        "ECG_results"
    ]
}
```

#### **Extraction Warnings**
Flags data quality issues:
```python
{
    "extraction_warnings": [
        "Symptoms lacking severity ratings",
        "Pain described without location",
        "Multiple abnormal vitals detected - possible systemic illness",
        "BMI indicates overweight category",
        "High fever with unusually low heart rate - possible measurement error"
    ]
}
```

**Why It Matters:**
- Highlights incomplete assessments
- Alerts clinicians to concerning patterns
- Flags potential data entry errors
- Improves overall data quality

---

### 7. **Improved SOAP Note Generation**

**Enhancements:**
- Includes height & BMI in patient demographics section
- Displays normal ranges alongside vital signs
- Integrates family history into subjective section
- Better anthropometric reporting

**Example Enhanced SOAP Note:**

```markdown
SUBJECTIVE:
48-year-old male presents with 3-day history of persistent cough, fever, 
and shortness of breath. Patient reports temperature reaching 39°C this morning. 
Denies chest pain. Reports no recent cough or respiratory symptoms. 
Smoking history: Former smoker, quit 5 years ago.
Family History: Father with coronary artery disease at age 65, 
                Mother with hypertension, Brother with type 2 diabetes

OBJECTIVE:
Height: 172 cm, Weight: 88 kg, BMI: 29.7 (Overweight)
Vital Signs:
- Temperature: 38.9°C (Normal: 37°C)
- Heart Rate: 115 bpm (Normal: 60-100)
- Respiratory Rate: 24 (Normal: 12-20) - ABNORMAL
- Blood Pressure: 145/92 mmHg (Normal: 120/80) - ABNORMAL
- Oxygen Saturation: 93% (Normal: 95-100%) - ABNORMAL

Physical Examination:
- General: Alert and oriented, moderate distress
- Lungs: Decreased breath sounds bilaterally

ASSESSMENT:
48-year-old male with fever, cough, dyspnea, and multiple abnormal vital signs 
concerning for acute respiratory infection with possible systemic illness. 
Overweight status noted (BMI 29.7). Significant family history of 
cardiovascular disease may warrant consideration.

Differential considerations:
- Community-acquired pneumonia
- Acute bronchitis
- Influenza
- COVID-19 infection

Abnormal findings requiring immediate attention:
- Hypoxia (93% SpO2)
- Tachycardia (115 bpm)
- Tachypnea (24 RR)
- Hypertension (145/92 mmHg)

PLAN:
1. Immediate physician evaluation recommended
2. Consider chest X-ray if respiratory infection suspected
3. Obtain rapid influenza/COVID testing if available
4. Monitor vitals closely, especially oxygen saturation
5. Ensure adequate hydration and rest
6. Follow-up medical evaluation within 24 hours if not admitted
```

---

## Data Model Changes

### Modified Files

#### **1. app/nlp/models/clinical_schema.py**
```python
# Enhanced PatientDemographics
class PatientDemographics(BaseModel):
    age: str
    sex: str
    weight_kg: float
    height_cm: float              # NEW
    bmi: float = Field(...)       # NEW - Auto-calculated

# Enhanced VitalSign
class VitalSign(BaseModel):
    name: str
    value: str
    unit: str                     # NEW
    normal_range: str             # NEW
    is_abnormal: bool             # NEW
    severity: Optional[Severity]  # Enhanced

# Enhanced Symptom
class Symptom(BaseModel):
    name: str
    severity: Severity
    onset: Optional[str]          # NEW
    location: Optional[str]       # NEW
    modifiers: List[str] = []     # NEW

# Enhanced MedicalHistory
class MedicalHistory(BaseModel):
    past_medical_conditions: List[str]
    current_medications: List[str]
    allergies: List[AllergyRecord]
    family_history: List[str]     # NEW
```

#### **2. app/nlp/src/symptom_extractor.py**
**Enhancements:**
- Height extraction from patient transcripts
- Automatic BMI calculation: `BMI = weight_kg / (height_cm/100)²`
- Family history extraction using LLM
- Integration with `ConfidenceCalculator` for weighted scoring
- Enhanced `_find_missing_fields()` method
- Added `_generate_warnings()` for data quality detection

**New Methods:**
```python
def _extract_height(self, text: str) -> Optional[float]
    """Extract height from patient transcript"""

def _calculate_bmi(self, weight_kg: float, height_cm: float) -> float
    """Calculate Body Mass Index"""

def _extract_family_history(self, text: str) -> List[str]
    """Extract family medical history from transcript"""

def _find_missing_fields(self, data: dict) -> List[str]
    """Identify critical missing clinical data"""

def _generate_warnings(self, data: dict) -> List[str]
    """Generate quality warnings for data issues"""
```

#### **3. app/nlp/src/confidence_calculator.py** (NEW)
**Purpose:** Weighted confidence calculation across components

**Key Classes:**
```python
class ConfidenceCalculator:
    def calculate_overall_confidence(
        self,
        symptoms_conf: float,
        vitals_conf: float,
        demographics_conf: float,
        history_conf: float
    ) -> float:
        """Calculate weighted confidence score"""

    def get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numerical score to HIGH/MEDIUM/LOW"""

    def generate_confidence_breakdown(self) -> dict:
        """Provide detailed confidence scoring explanation"""
```

#### **4. app/nlp/src/soap_formatter.py** (Enhanced)
**Improvements:**
- Display height & BMI in subjective section
- Show normal ranges for vital signs in objective section
- Include family history in medical context
- Better anthropometric reporting
- Enhanced critical flags section

**New Formatting Features:**
```python
def _format_demographics_with_bmi(self, data: PatientDemographics) -> str
    """Include BMI in demographics section"""

def _format_vitals_with_ranges(self, vitals: List[VitalSign]) -> str
    """Display vitals with normal ranges for context"""

def _format_clinical_flags(self, flags: List[ClinicalFlag]) -> str
    """Highlight critical findings requiring attention"""
```

---

## Clinical Impact

### Improved Patient Safety
- Multiple validation checks catch data entry errors
- Confidence scores prevent reliance on uncertain data
- Family history integration enables better risk assessment
- Automatic BMI calculation identifies nutrition-related concerns

### Better Clinical Documentation
- SOAP notes follow international standards
- Complete anthropometric data improves medication dosing
- Family history provides genetic risk context
- Clinical flags highlight urgent concerns

### Enhanced Data Quality
- Missing fields alerts ensure complete assessments
- Quality warnings catch suspicious patterns
- Confidence scores drive additional data collection
- Multi-factor validation improves accuracy

---

## Integration Example

```python
# Complete workflow using new enhancements
from models.clinical_schema import PatientDemographics, Symptom, VitalSign
from src.symptom_extractor import SymptomsExtractor
from src.confidence_calculator import ConfidenceCalculator
from src.soap_formatter import SOAPFormatter

# 1. Extract from transcript
extractor = SymptomsExtractor()
structured_data = extractor.extract(
    transcript="Patient reports 3-day fever and cough...",
    demographics=PatientDemographics(
        age="48", sex="male", weight_kg=88, height_cm=172
    )  # height_cm used for BMI calculation
)

# 2. Check confidence
confidence = ConfidenceCalculator()
conf_level = confidence.calculate_overall_confidence(
    symptoms_conf=0.92,
    vitals_conf=0.88,
    demographics_conf=0.99,
    history_conf=0.76
)
# Returns: 0.87 (HIGH confidence)

# 3. Generate SOAP note with enhancements
formatter = SOAPFormatter()
soap_note = formatter.format(structured_data)

# Output includes:
# - BMI and anthropometric data
# - Normal ranges for vital signs
# - Family history context
# - Clinical flags for urgent findings
```

---


## Backward Compatibility

All enhancements are backward compatible:
- Optional fields don't break existing integrations
- Legacy requests still work without height/family_history
- Confidence scoring is automatically calculated if missing
- SOAP formatting gracefully handles missing fields

---

