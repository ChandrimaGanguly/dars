"""Error handling framework for standardized API responses.

This module provides:
- Custom exception classes
- Error codes following API_ARCHITECTURE.md Part 4
- FastAPI exception handlers
"""

from src.errors.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DarsAPIException,
    ExternalServiceError,
    ResourceNotFoundError,
    StateConflictError,
    ValidationError,
)
from src.errors.handlers import (
    dars_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    register_exception_handlers,
    validation_exception_handler,
)

__all__ = [
    # Exceptions (sorted)
    "AuthenticationError",
    "AuthorizationError",
    "DarsAPIException",
    "ExternalServiceError",
    "ResourceNotFoundError",
    "StateConflictError",
    "ValidationError",
    # Handlers (sorted)
    "dars_exception_handler",
    "generic_exception_handler",
    "http_exception_handler",
    "register_exception_handlers",
    "validation_exception_handler",
]
