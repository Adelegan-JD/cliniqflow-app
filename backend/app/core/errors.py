from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def error_envelope(code: str, message: str, details: Any = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Extract user-friendly error messages from validation errors
    errors = exc.errors()
    
    # Build a readable message from field errors
    field_errors = []
    for error in errors:
        field_path = " > ".join(str(x) for x in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        
        # Format message based on error type
        if error.get("type") == "string_too_short":
            ctx = error.get("ctx", {})
            min_len = ctx.get("min_length", 1)
            field_errors.append(f"{field_path.split('>')[-1].strip()} must be at least {min_len} characters")
        elif error.get("type") == "string_too_long":
            ctx = error.get("ctx", {})
            max_len = ctx.get("max_length", 1)
            field_errors.append(f"{field_path.split('>')[-1].strip()} must be at most {max_len} characters")
        elif error.get("type") == "value_error":
            field_errors.append(f"{field_path.split('>')[-1].strip()}: {msg}")
        else:
            field_errors.append(msg)
    
    # Create a readable error message
    error_message = field_errors[0] if field_errors else "Request validation failed"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_envelope(
            "validation_error",
            error_message,
            field_errors if len(field_errors) > 1 else None,
        ),
    )


async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_envelope("internal_error", "An unexpected error occurred", None),
    )
