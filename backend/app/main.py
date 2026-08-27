from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    admin,
    billing,
    clinical_forms,
    consultation,
    doctor,
    discharge,
    health,
    hospital,
    nurse,
    medications,
    orchestration,
    orders,
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

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    # Empty configuration means cross-origin browsers are denied. Production
    # origins are configured per environment, never hard-coded in source.
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
async def validate_runtime_configuration() -> None:
    settings.validate_production()
# "http://localhost:5173", "https://app.cliniq-flow.com" - origins for frontend on localhost and server

app.include_router(health.router)
app.include_router(hospital.router)
app.include_router(billing.router)
app.include_router(clinical_forms.router)
app.include_router(orders.router)
app.include_router(medications.router)
app.include_router(discharge.router)
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
