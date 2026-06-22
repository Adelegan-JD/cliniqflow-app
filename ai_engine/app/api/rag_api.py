"""
RAG (Retrieval-Augmented Generation) API router.
Mounted at /rag in main.py

Endpoints:
  POST /rag/retrieve     — query medication knowledge base, get evidence
  POST /rag/validate-dose — check dose safety using deterministic rules
"""

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.Rag.dose_validator import DoseAssessmentResult, assess_dose
from app.Rag.llmengine import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG & Medication Validation"])

# Initialize RAG engine (lazy load on first request)
_rag_engine: Optional[RAGEngine] = None
_docs_path = Path("app/rag/files")  # Adjust path as needed

def _get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine(
            docs_path=str(_docs_path),
            use_embeddings=False,  # Start with keyword search
            openai_api_key=None,   # No LLM for now
        )
    return _rag_engine


#  Pydantic schemas 

class RetrieveRequest(BaseModel):
    query: str = Field(..., description="Medication or dosing question", example="What is the pediatric amoxicillin dosing range?")
    top_k: Optional[int] = Field(5, description="Number of top results to return", ge=1, le=20)


class RetrievalResult(BaseModel):
    chunk_id: str
    source: str
    page: Optional[int]
    score: float
    text: str
    metadata: dict


class RetrieveResponse(BaseModel):
    query: str
    results: List[RetrievalResult]
    retrieved_count: int
    processing_time_ms: float


class ValidateDoseRequest(BaseModel):
    drug_name: str = Field(..., description="Medication name", example="Amoxicillin")
    dose_mg: Optional[float] = Field(None, description="Single dose in mg", gt=0)
    frequency_per_day: Optional[int] = Field(None, description="Doses per day", gt=0)
    patient_weight_kg: Optional[float] = Field(None, description="Patient weight in kg", gt=0)
    patient_age_years: Optional[float] = Field(None, description="Patient age in years", gt=0)
    route: Optional[str] = Field(None, description="Administration route", example="oral")


class ValidateDoseResponse(BaseModel):
    drug_name: str
    normalized_drug_name: Optional[str]
    patient_age_years: Optional[float]
    patient_weight_kg: Optional[float]
    dose_mg: Optional[float]
    frequency_per_day: Optional[int]
    total_daily_mg: Optional[float]
    mgkg_per_day: Optional[float]
    safety_level: str
    reasons: List[str]
    recommended_min_mgkg: Optional[float]
    recommended_max_mgkg: Optional[float]
    max_daily_mg: Optional[float]
    note: Optional[str]
    processing_time_ms: float


# ── Routes 

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_evidence(request: RetrieveRequest) -> RetrieveResponse:
    """
    Query the medication knowledge base for relevant evidence.
    Returns top-k matching document chunks with relevance scores.
    """
    import time
    start = time.perf_counter()

    try:
        engine = _get_rag_engine()
        results = engine.retrieve(request.query, top_k=request.top_k)

        response_results = [
            RetrievalResult(
                chunk_id=result.chunk_id,
                source=result.source,
                page=result.page,
                score=result.score,
                text=result.text,
                metadata=result.metadata,
            )
            for result in results
        ]

        elapsed_ms = (time.perf_counter() - start) * 1000

        return RetrieveResponse(
            query=request.query,
            results=response_results,
            retrieved_count=len(response_results),
            processing_time_ms=round(elapsed_ms, 2),
        )

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.post("/validate-dose", response_model=ValidateDoseResponse)
async def validate_dose(request: ValidateDoseRequest) -> ValidateDoseResponse:
    """
    Validate medication dose safety using deterministic clinical rules.
    Returns safety assessment with reasons and recommendations.
    """
    import time
    start = time.perf_counter()

    try:
        result = assess_dose(
            drug_name=request.drug_name,
            dose_mg=request.dose_mg,
            frequency_per_day=request.frequency_per_day,
            patient_weight_kg=request.patient_weight_kg,
            patient_age_years=request.patient_age_years,
            route=request.route,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        return ValidateDoseResponse(
            drug_name=result.drug_name,
            normalized_drug_name=result.normalized_drug_name,
            patient_age_years=result.patient_age_years,
            patient_weight_kg=result.patient_weight_kg,
            dose_mg=result.dose_mg,
            frequency_per_day=result.frequency_per_day,
            total_daily_mg=result.total_daily_mg,
            mgkg_per_day=result.mgkg_per_day,
            safety_level=result.safety_level.value,
            reasons=result.reasons,
            recommended_min_mgkg=result.recommended_min_mgkg,
            recommended_max_mgkg=result.recommended_max_mgkg,
            max_daily_mg=result.max_daily_mg,
            note=result.note,
            processing_time_ms=round(elapsed_ms, 2),
        )

    except Exception as e:
        logger.error(f"Dose validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dose validation failed: {str(e)}")