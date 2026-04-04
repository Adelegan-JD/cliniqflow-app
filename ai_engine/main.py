# import os as os
# import torch

# # This helps Python find the torch binaries if they are hidden
# os.add_dll_directory(os.path.join(os.environ['VIRTUAL_ENV'], 'Lib', 'site-packages', 'torch', 'lib'))

from app.asr.asr_engine import (
    ModelManager,
    download_model_if_needed,
)

# Standard imports 
import logging
import os
import time
from contextlib import asynccontextmanager

import torch
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pyannote.audio import Pipeline as DiarizationPipeline
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# API routers 
from app.api.asr_api       import router as asr_router

load_dotenv()

# Config 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

API_KEY         = os.environ.get("openai_key", "openai_key")
HF_TOKEN        = os.environ.get("HF_TOKEN")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000").split(",")


# load models once at startup 
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up...")
    t0 = time.time()

    mm        = ModelManager()
    mm.device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {mm.device}")

    local_path = download_model_if_needed()

    mm.processor = WhisperProcessor.from_pretrained(local_path, local_files_only=True)
    mm.model = WhisperForConditionalGeneration.from_pretrained(
        local_path,
        local_files_only=True,
        torch_dtype=torch.float16 if mm.device == "cuda" else torch.float32,
    ).to(mm.device)
    mm.model.eval()
    logger.info("Whisper loaded ✓")

    mm.diarizer = DiarizationPipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1"
    ).to(torch.device(mm.device))
    logger.info("pyannote diarizer loaded ✓")

    mm.model_loaded          = True
    app.state.model_manager  = mm         
    logger.info(f"Ready in {round(time.time()-t0, 2)}s")

    yield 

    logger.info("Shutting down...")
    del mm.model, mm.processor, mm.diarizer
    if mm.device == "cuda":
        torch.cuda.empty_cache()
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
    if credentials.credentials != API_KEY:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


# Register routers 
app.include_router(asr_router,dependencies=[Depends(verify_api_key)])



@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "CLINIQ-FLOW AI Engine",
        "version": "1.0.0",
        "docs":    "/docs",
        "routes":  ["/asr", "/soap", "/medication", "/triage"],
    }

@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok"}
