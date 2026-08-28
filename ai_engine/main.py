
from __future__ import annotations

from app.asr.asr_engine import (
    ModelManager,
    load_model,
)

# Standard imports 
import logging
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# API routers 
from app.api.asr_api       import router as asr_router
from app.nlp.api.nlp_routes import router as nlp_router
from app.api.rag_api       import router as rag_router

load_dotenv()

# Config 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

API_KEY = os.environ.get("AI_ENGINE_TOKEN")
ENABLE_DIARIZATION = os.environ.get("ASR_ENABLE_DIARIZATION", "false").lower() in {"1", "true", "yes"}
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000").split(",")


# load models once at startup 
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up...")
    t0 = time.time()

    if ENABLE_DIARIZATION:
        logger.warning("ASR_ENABLE_DIARIZATION is ignored in the compact production runtime")
    mm = load_model()
    logger.info("Speaker diarization disabled; using a single-speaker transcript")
    app.state.model_manager  = mm         
    logger.info(f"Ready in {round(time.time()-t0, 2)}s")

    yield 

    logger.info("Shutting down...")
    del mm.model
    logger.info("Shutdown complete.")


# App
app = FastAPI(
    title="CLINIQ-FLOW AI Engine",
    description="AI-assisted clinical workflow — transcription, SOAP notes, triage, medication validation",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="AI engine token is not configured")
    if credentials.credentials != API_KEY:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


# Register routers 
# The AI engine is an internal service.  Every inference endpoint requires the
# backend service token; browsers never call this service directly.
app.include_router(asr_router, dependencies=[Depends(verify_api_key)])
app.include_router(nlp_router, dependencies=[Depends(verify_api_key)])
app.include_router(rag_router, dependencies=[Depends(verify_api_key)])



@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "CLINIQ-FLOW AI Engine",
        "version": "1.0.0",
        "docs":    "/docs",
        "routes":  ["/asr", "/nlp", "/rag"],
    }

@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok"}
