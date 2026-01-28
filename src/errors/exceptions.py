"""Custom exception classes for the Dars API.

All exceptions follow the error response format from API_ARCHITECTURE.md Part 4:
{
  "error": ErrorType,
  "message": str,
  "error_code": str,
  "details": dict | None,
  "timestamp": str,
  "request_id": str
}
"""

from typing import Any


class DarsAPIException(Exception):
    """Base exception for all Dars API errors.

    All custom exceptions should inherit from this class to enable
    consistent error handling and response formatting.

    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code (e.g., ERR_AUTH_FAILED).
        status_code: HTTP status code for the error.
        details: Optional additional error details.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            status_code: HTTP status code (default: 500).
            details: Optional additional error details.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


# Authentication & Authorization Errors (401, 403)


class AuthenticationError(DarsAPIException):
    """Authentication failed (401)."""

    def __init__(
        self, message: str = "Authentication required", error_code: str = "ERR_AUTH_FAILED"
    ) -> None:
        """Initialize authentication error.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
        """
        super().__init__(message=message, error_code=error_code, status_code=401)


class AuthorizationError(DarsAPIException):
    """Authorization failed (403)."""

    def __init__(
        self, message: str = "Not authorized for this resource", error_code: str = "ERR_ADMIN_ONLY"
    ) -> None:
        """Initialize authorization error.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
        """
        super().__init__(message=message, error_code=error_code, status_code=403)


# Validation Errors (400)


class ValidationError(DarsAPIException):
    """Input validation failed (400)."""

    def __init__(
        self,
        message: str = "Invalid request parameters",
        error_code: str = "ERR_INVALID_PARAM",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            details: Optional validation details (e.g., field errors).
        """
        super().__init__(message=message, error_code=error_code, status_code=400, details=details)


# Resource Not Found Errors (404)


class ResourceNotFoundError(DarsAPIException):
    """Requested resource not found (404)."""

    def __init__(
        self, message: str = "Resource not found", error_code: str = "ERR_RESOURCE_NOT_FOUND"
    ) -> None:
        """Initialize resource not found error.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
        """
        super().__init__(message=message, error_code=error_code, status_code=404)


# State Conflict Errors (409)


class StateConflictError(DarsAPIException):
    """Resource state conflict (409)."""

    def __init__(
        self, message: str = "Resource state conflict", error_code: str = "ERR_STATE_CONFLICT"
    ) -> None:
        """Initialize state conflict error.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
        """
        super().__init__(message=message, error_code=error_code, status_code=409)


# External Service Errors (503)


class ExternalServiceError(DarsAPIException):
    """External service unavailable or failed (503)."""

    def __init__(
        self,
        message: str = "External service unavailable",
        error_code: str = "ERR_EXTERNAL_SERVICE",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize external service error.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            details: Optional details about the service failure.
        """
        super().__init__(message=message, error_code=error_code, status_code=503, details=details)


# Specific Error Codes (from API_ARCHITECTURE.md Part 4)

# Auth errors
ERR_AUTH_FAILED = "ERR_AUTH_FAILED"
ERR_AUTH_MISSING = "ERR_AUTH_MISSING"
ERR_ADMIN_ONLY = "ERR_ADMIN_ONLY"

# Validation errors
ERR_INVALID_JSON = "ERR_INVALID_JSON"
ERR_INVALID_PARAM = "ERR_INVALID_PARAM"
ERR_INVALID_GRADE = "ERR_INVALID_GRADE"
ERR_INVALID_LANGUAGE = "ERR_INVALID_LANGUAGE"
ERR_INVALID_ANSWER_FORMAT = "ERR_INVALID_ANSWER_FORMAT"

# Resource errors
ERR_STUDENT_NOT_FOUND = "ERR_STUDENT_NOT_FOUND"
ERR_PROBLEM_NOT_FOUND = "ERR_PROBLEM_NOT_FOUND"
ERR_SESSION_NOT_FOUND = "ERR_SESSION_NOT_FOUND"
ERR_SESSION_EXPIRED = "ERR_SESSION_EXPIRED"

# State errors
ERR_SESSION_ALREADY_ACTIVE = "ERR_SESSION_ALREADY_ACTIVE"
ERR_SESSION_ALREADY_COMPLETED = "ERR_SESSION_ALREADY_COMPLETED"
ERR_DUPLICATE_RESPONSE = "ERR_DUPLICATE_RESPONSE"
ERR_HINT_LIMIT_EXCEEDED = "ERR_HINT_LIMIT_EXCEEDED"

# External service errors
ERR_CLAUDE_API_FAILED = "ERR_CLAUDE_API_FAILED"
ERR_CLAUDE_TIMEOUT = "ERR_CLAUDE_TIMEOUT"
ERR_TELEGRAM_API_FAILED = "ERR_TELEGRAM_API_FAILED"
ERR_DATABASE_ERROR = "ERR_DATABASE_ERROR"

# Internal errors
ERR_INTERNAL = "ERR_INTERNAL"
