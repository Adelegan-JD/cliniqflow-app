# CliniqFlow AI Engine - Code Documentation

This document describes the AI Engine service only (ASR, NLP, and RAG). It reflects the code currently in the ai_engine folder.

## Scope and responsibilities

The AI Engine provides:

- NLP clinical structuring: vitals urgency scoring, transcript parsing, SOAP note formatting, confidence scoring, and validation.
- ASR: Whisper transcription with speaker diarization (pyannote).
- RAG: medication knowledge retrieval plus deterministic dose validation.

This service is a decision-support tool. It does not diagnose or prescribe.

## Entry point and lifecycle

File: main.py

Key responsibilities:

- App initialization and router registration.
- Model loading during startup (Whisper + pyannote), stored on app.state.model_manager.
- CORS configuration using ALLOWED_ORIGINS.
- Rate limiting with slowapi (default 60/minute).
- ASR authentication (Bearer token check using openai_key env var).

Startup flow:

1. Create ModelManager and set device to cuda if available.
2. Download Whisper model on first run (cached in CACHE_DIR).
3. Load Whisper processor and model.
4. Load pyannote diarization pipeline.
5. Expose routers:
   - /asr (protected)
   - /nlp
   - /rag

## Folder structure (ai_engine)

```
ai_engine/
  app/
    api/
      asr_api.py
      rag_api.py
    asr/
      asr_engine.py
      asr_service.py
    nlp/
      api/
        nlp_routes.py
      models/
        clinical_schema.py
      src/
        symptom_extractor.py
        urgency_scorer.py
        soap_formatter.py
        confidence_calculator.py
        validators.py
      image/
        Road Map.png
    Rag/
      files/                # medication knowledge base
      chunker.py
      loader.py
      indexer.py
      retriever.py
      llmengine.py
      prompter.py
      dose_validator.py
      models.py
      test_dose_validator.py
  main.py
  requirements.txt
  .env.example
```

Note: the RAG package lives in app/Rag but is imported as app.rag in code. This works on Windows file systems.

## API endpoints

Root and health:

- GET / : returns service info and route list.
- GET /health : returns overall health status.

ASR (requires Authorization: Bearer <openai_key>):

- GET /asr/health
  - Returns model load state and device.
- POST /asr/transcribe
  - Upload audio file (wav, mp3, mp4, webm, ogg; max 50 MB).
  - Audio is resampled to 16 kHz mono.
  - Returns diarized segments and a formatted transcript.
  - Rate limited to 10/minute.

NLP:

- POST /nlp/vitals-urgency
  - Nurse vitals in, urgency score and abnormal vitals out.
- POST /nlp/nurse-to-doctor
  - Merges nurse vitals with transcript (if provided), produces SOAP + validation.
- POST /nlp/process
  - Full transcript pipeline (legacy path kept for compatibility).
- GET /nlp/health
  - Returns NLP workflow metadata.

RAG:

- POST /rag/retrieve
  - Keyword retrieval over medication documents.
  - Returns top-k evidence chunks.
- POST /rag/validate-dose
  - Deterministic dose safety validation.
  - Returns safety level, reasons, and recommended ranges.

## NLP pipeline (app/nlp)

Key modules:

- symptom_extractor.py
  - Rule-based extraction using keyword dictionaries and regex.
  - Optional LLM extraction using OPENAI_API_KEY.
  - Hybrid merge strategy with fallback to rule-based output.
  - Detects clinical flags (danger signs, abnormal vitals, cardiac risk patterns).

- urgency_scorer.py
  - Age-aware scoring for temperature, heart rate, respiratory rate, blood pressure, and SpO2.
  - Produces UrgencyScore (level, score, reasons, abnormal_vitals).

- confidence_calculator.py
  - Weighted confidence calculation across symptoms, vitals, demographics, and history.

- soap_formatter.py
  - Formats SOAP notes with safety disclaimers.
  - Accepts optional nurse vitals and inserts them into Objective section.

- validators.py
  - StructuredDataValidator and SOAPNoteValidator enforce safety rules.
  - FallbackTrigger flags low-confidence or low-quality outputs.
  - ClinicalValidator merges results for API responses.

Workflow highlights:

- Nurse vitals -> urgency scoring (fast triage).
- Nurse-to-doctor handoff -> SOAP note with nurse vitals embedded.
- Full transcript processing -> structured data, SOAP, validation.

## ASR pipeline (app/asr)

Key modules:

- asr_engine.py
  - ModelManager stores Whisper processor, model, and pyannote diarizer.
  - download_model_if_needed() caches Whisper small model to CACHE_DIR.
  - diarize_and_transcribe() runs pyannote first, then Whisper per speaker segment.
  - format_conversation() produces a readable speaker-labeled transcript.

- asr_service.py
  - Wrapper around ModelManager for readiness checks and formatting convenience.

- asr_api.py
  - Validates file type and size.
  - Loads and resamples audio (librosa, 16 kHz mono).
  - Returns speaker segments and merged conversation text.

## RAG pipeline (app/Rag)

Key modules:

- loader.py
  - Loads TXT, PDF, DOCX, and JSON from app/Rag/files.
  - Normalizes whitespace and builds DocumentRecord objects.

- chunker.py
  - Splits documents into overlapping word-based chunks.

- indexer.py
  - SimpleIndexer: keyword overlap scoring.
  - EmbeddingIndexer: OpenAI embeddings (text-embedding-3-small).

- retriever.py
  - Chooses indexer and returns top-k RetrievalResult objects.

- prompter.py
  - Builds a safe, constrained prompt for LLM answers.

- llmengine.py
  - RAGEngine orchestrates loading, chunking, retrieval, and optional LLM answers.
  - In the API, retrieval is used; LLM answers are optional if an API key is provided.

- dose_validator.py
  - Deterministic rule-based medication safety checks.
  - Parses age, weight, dose, frequency, and routes.
  - Returns DoseAssessmentResult with safety level and reasons.

## Data models

NLP models (app/nlp/models/clinical_schema.py):

- Symptom, VitalSign, PatientDemographics, MedicalHistory, ClinicalFlag
- StructuredClinicalData (primary output)
- SOAPNote (formatted note with disclaimer)
- ValidationResult (errors, warnings, missing fields)
- ExtractionMethod and ConfidenceLevel enums

RAG models (app/Rag/models.py):

- DocumentRecord, DocumentChunk
- RetrievalResult
- LLMAnswer

ASR responses are defined in asr_api.py using Pydantic response models.

## Configuration (environment variables)

Defined in .env.example:

- openai_key: required Bearer token for ASR endpoints.
- OPENAI_API_KEY: optional, enables LLM-based NLP extraction and RAG answers.
- HF_TOKEN: required to download pyannote diarization models.
- ALLOWED_ORIGINS: comma-separated list for CORS.

Additional runtime settings:

- CACHE_DIR: Whisper cache directory (default ./model_cache).

## Running and testing

Run locally:

```
cd ai_engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Tests:

```
pytest
```

Note: first ASR startup downloads Whisper and pyannote models and may take time.

## Safety and compliance

- NLP output avoids diagnosis and treatment instructions by design.
- validators.py enforces safety rules and flags potential violations.
- RAG prompts explicitly forbid dose generation and prescriptions; dose validation is deterministic only.