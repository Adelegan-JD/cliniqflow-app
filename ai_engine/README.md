# CliniqFlow AI Engine

CliniqFlow AI Engine is the standalone FastAPI service that powers clinical NLP, speech-to-text (ASR), and medication guidance for the CliniqFlow platform. It is designed to be called by the backend API (or trusted clients) and exposes a focused set of endpoints for triage support, transcript structuring, and dose validation.

This service is a decision-support tool. It organizes and flags clinical information, but does not diagnose.

## What it does

- NLP for clinical structuring
  - Vitals-based urgency scoring for nurse triage
  - Transcript-to-structured data and SOAP note generation
  - Nurse-to-doctor handoff that merges vitals with narrative
- ASR (Automatic Speech Recognition)
  - Offline int8 CTranslate2 transcription using the approved `LyngualLabs/whisper-small-yoruba` checkpoint
  - Automatic Yoruba, English and mixed-language detection
  - A single clinical-speaker stream; speaker diarization is intentionally not included in the compact production runtime
- RAG medication guidance
  - Retrieve evidence from curated medication documents
  - Deterministic dose validation with safety checks

## NLP pipeline and outputs

- Extraction methods
  - Rule-based extraction for speed and deterministic behavior
  - Offline rule-based extraction with confidence-aware warnings
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

All AI inference endpoints (ASR, NLP and RAG) require a Bearer token. The token value comes from the `AI_ENGINE_TOKEN` environment variable; it is an internal service token, not an OpenAI key. The browser must call the backend only; the backend forwards this token to the AI engine.

Example header:

```
Authorization: Bearer <AI_ENGINE_TOKEN>
```
Do not expose the AI-engine port publicly in production.

## Environment variables

- AI_ENGINE_TOKEN: token used to authorize ASR requests (required for ASR)
- ASR_MODEL_PATH: path to the embedded converted model (default: `/opt/models/yoruba-whisper-small-ct2`)
- ASR_DEVICE: `cpu` for the compact deployment
- ASR_COMPUTE_TYPE: `int8` for the compact deployment
- ASR_ENABLE_DIARIZATION: retained for configuration compatibility but ignored by the compact production runtime


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
│   ├── asr/                      # Compact offline Whisper runtime
│   ├── nlp/
│   │   ├── api/                  # NLP endpoints
│   │   ├── models/               # Pydantic clinical schemas
│   │   └── src/                  # Extractors, scorers, formatters
│   └── Rag/
│       ├── files/                # Medication knowledge sources
│       └── ...
├── main.py                       # FastAPI app + model boot
├── Dockerfile                    # Converts and embeds the model during image build
├── fly.toml                      # Fly.io deployment configuration
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

For the production-equivalent local test, build and run the Docker image. The image embeds the converted model and tokenizer, so it does not download model assets at startup.

## Testing

```
pytest
```

## Troubleshooting

- If ASR requests return 401 or 503, confirm `AI_ENGINE_TOKEN` is set and the Bearer token matches.
- If NLP or RAG requests return 401, confirm they are being made by the backend with the configured internal service token.
- If startup says the model is missing, confirm the Docker build completed and `ASR_MODEL_PATH` points to the converted model directory.
- The compact service runs on CPU with int8 quantization and intentionally has no speaker diarization.
