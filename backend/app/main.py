from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    admin,
    consultation,
    doctor,
    health,
    nurse,
    orchestration,
    patients,
    record_officer,
    visits,
)
from app.core.config import settings
from app.core.errors import error_envelope, generic_exception_handler, validation_exception_handler

app = FastAPI(
    title="Cliniq Flow API",
    description="Public REST API for the Cliniq Flow frontend (paediatric workflows, orchestration to AI engine).",
    version="0.1.0",
)

#origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

origins = [
    "http://192.168.18.9:5173",  # Your Vite frontend IP
    "http://localhost:5173",     # Localhost frontend
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.cliniq-flow.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(admin.router)
app.include_router(consultation.router)
app.include_router(doctor.router)
app.include_router(record_officer.router)
app.include_router(nurse.router)
app.include_router(visits.router)
app.include_router(patients.router)
app.include_router(orchestration.router_ai)
app.include_router(orchestration.router_nlp)
app.include_router(orchestration.router_asr)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope("http_error", message, None),
    )


app.add_exception_handler(RequestValidationError, validation_exception_handler) #type: ignore
app.add_exception_handler(Exception, generic_exception_handler)
