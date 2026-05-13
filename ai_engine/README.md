# CliniqFlow AI Engine

CliniqFlow AI Engine is the standalone FastAPI service that powers clinical NLP, speech-to-text (ASR), and medication guidance for the CliniqFlow platform. It is designed to be called by the backend API (or trusted clients) and exposes a focused set of endpoints for triage support, transcript structuring, and dose validation.

This service is a decision-support tool. It organizes and flags clinical information, but does not diagnose.

## What it does

- NLP for clinical structuring
  - Vitals-based urgency scoring for nurse triage
  - Transcript-to-structured data and SOAP note generation
  - Nurse-to-doctor handoff that merges vitals with narrative
- ASR (Automatic Speech Recognition)
  - Whisper-based transcription
  - Speaker diarization using pyannote
- RAG medication guidance
  - Retrieve evidence from curated medication documents
  - Deterministic dose validation with safety checks

## NLP pipeline and outputs

- Extraction methods
  - Rule-based extraction for speed and deterministic behavior
  - Optional LLM extraction when `OPENAI_API_KEY` is set
  - Hybrid merge with confidence-aware fallback to rule-based results
- Structured outputs
  - Demographics include height and auto-calculated BMI
  - Symptoms include onset, location, and modifiers when present
  - Vitals include unit, normal range, and abnormality flags
  - Medical history includes family history when available
  - Clinical flags highlight urgent findings
- Quality and confidence signals
  - `overall_confidence` and `confidence_level` (high, medium, low)
  - `missing_fields` for incomplete assessments
  - `extraction_warnings` for suspicious or low-quality inputs

Confidence weighting used for NLP scoring:

```
symptoms:     0.40
vitals:       0.30
demographics: 0.15
history:      0.15
```

## API overview


NLP
- POST /nlp/vitals-urgency
- POST /nlp/nurse-to-doctor
- POST /nlp/process
- GET  /nlp/health

ASR (requires Bearer token)
- GET  /asr/health
- POST /asr/transcribe

RAG
- POST /rag/retrieve
- POST /rag/validate-dose


## Authentication

ASR endpoints require a Bearer token. The token value comes from the `openai_key` environment variable.

Example header:

```
Authorization: Bearer <openai_key>
```
NLP and RAG endpoints currently do not require a token in this service.

## Environment variables

- openai_key: API key used to authorize ASR requests (required for ASR)
- OPENAI_API_KEY: optional key for LLM-based symptom extraction
- HF_TOKEN: Hugging Face token required for pyannote diarization models


## Example requests

Vitals urgency:

```json
POST /nlp/vitals-urgency
{
  "patient_age": "35 years",
  "patient_sex": "female",
  "temperature": 39.2,
  "heart_rate": 128,
  "respiratory_rate": 26,
  "oxygen_saturation": 93,
  "weight_kg": 70,
  "height_cm": 165
}
```

Example response (trimmed):

```json
{
  "session_id": "vitals-1715510000000",
  "urgency_level": "emergency",
  "urgency_score": 78,
  "urgency_reasons": ["Fever", "Tachycardia", "Hypoxia"],
  "abnormal_vitals": ["temperature", "heart_rate", "oxygen_saturation"],
  "bmi": 25.71,
  "bmi_category": "Overweight"
}
```

Transcript processing:

```json
POST /nlp/process
{
  "transcript": "Patient reports 3 days of fever and cough...",
  "patient_age": "42 years",
  "patient_sex": "male",
  "session_id": "session_123"
}
```

Example response (trimmed):

```json
{
  "session_id": "session_123",
  "structured_data": {
    "overall_confidence": 0.85,
    "confidence_level": "high",
    "missing_fields": ["oxygen_saturation"],
    "extraction_warnings": []
  },
  "soap_note": {
    "subjective": "...",
    "objective": "...",
    "assessment": "...",
    "plan": "..."
  }
}
```


## Folder structure

```
ai_engine/
├── app/
│   ├── api/
│   │   ├── asr_api.py            # ASR endpoints
│   │   └── rag_api.py            # RAG endpoints
│   ├── asr/                      # Whisper + diarization
│   ├── nlp/
│   │   ├── api/                  # NLP endpoints
│   │   ├── models/               # Pydantic clinical schemas
│   │   └── src/                  # Extractors, scorers, formatters
│   └── Rag/
│       ├── files/                # Medication knowledge sources
│       └── ...
├── main.py                       # FastAPI app + model boot
├── requirements.txt
└── README.md
```

## Run locally (Windows PowerShell)

```
cd ai_engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Notes:
- First run may download Whisper and pyannote models.
- GPU is used automatically if available; otherwise CPU is used.

## Testing

```
pytest
```

## Troubleshooting

- If ASR requests return 401, confirm `openai_key` is set and the Bearer token matches.
- If diarization fails, verify `HF_TOKEN` is set and has access to required models.
- If LLM extraction is disabled, set `OPENAI_API_KEY` (rule-based extraction still works).
