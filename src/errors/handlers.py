"""FastAPI exception handlers for standardized error responses.

All error responses follow the format from API_ARCHITECTURE.md Part 4:
{
  "error": ErrorType,
  "message": str,
  "error_code": str,
  "details": dict | None,
  "timestamp": str,
  "request_id": str
}
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.errors.exceptions import DarsAPIException


def map_status_to_error_type(status_code: int) -> str:
    """Map HTTP status code to error type string.

    Args:
        status_code: HTTP status code.

    Returns:
        Error type string (e.g., "bad_request", "unauthorized").
    """
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        500: "internal_error",
        503: "service_unavailable",
    }
    return mapping.get(status_code, "internal_error")


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = "ERR_UNKNOWN",
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Create a standardized error response.

    Args:
        status_code: HTTP status code.
        message: Human-readable error message.
        error_code: Machine-readable error code.
        details: Optional additional error details.
        request_id: Optional request ID for tracing.

    Returns:
        JSONResponse with standardized error format.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": map_status_to_error_type(status_code),
            "message": message,
            "error_code": error_code,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id or str(uuid.uuid4()),
        },
    )


async def dars_exception_handler(request: Request, exc: DarsAPIException) -> JSONResponse:
    """Handle custom DarsAPIException errors.

    Args:
        request: FastAPI request object.
        exc: DarsAPIException instance.

    Returns:
        JSONResponse with error details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        request_id=request_id,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette/FastAPI HTTPException errors.

    Args:
        request: FastAPI request object.
        exc: HTTPException instance.

    Returns:
        JSONResponse with error details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return create_error_response(
        status_code=exc.status_code,
        message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
        error_code=getattr(exc, "error_code", "ERR_UNKNOWN"),
        request_id=request_id,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: FastAPI request object.
        exc: RequestValidationError instance.

    Returns:
        JSONResponse with validation error details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Format validation errors for better readability
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})

    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid request parameters",
        error_code="ERR_INVALID_PARAM",
        details={"validation_errors": errors},
        request_id=request_id,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: FastAPI request object.
        exc: Generic Exception instance.

    Returns:
        JSONResponse with generic error message.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log the full exception for debugging
    # (In production, this would be sent to a logging service)
    import traceback

    traceback_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"[ERROR] Unhandled exception for request {request_id}: {traceback_str}")

    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        error_code="ERR_INTERNAL",
        details={"exception_type": type(exc).__name__} if exc else None,
        request_id=request_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance.
    """
    app.add_exception_handler(DarsAPIException, dars_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
