"""Unit tests for error handling framework.

Tests:
- Custom exception classes
- Error response formatting
- Exception handlers
"""

import pytest
from fastapi import HTTPException, Request

from src.errors.exceptions import (
    ERR_ADMIN_ONLY,
    ERR_AUTH_FAILED,
    ERR_CLAUDE_TIMEOUT,
    AuthenticationError,
    AuthorizationError,
    DarsAPIException,
    ExternalServiceError,
    ResourceNotFoundError,
    StateConflictError,
)
from src.errors.exceptions import (
    ValidationError as DarsValidationError,
)
from src.errors.handlers import (
    create_error_response,
    dars_exception_handler,
    http_exception_handler,
    map_status_to_error_type,
)


@pytest.mark.unit
class TestExceptions:
    """Tests for custom exception classes."""

    def test_dars_api_exception(self) -> None:
        """Test base DarsAPIException."""
        exc = DarsAPIException(
            message="Test error",
            error_code="ERR_TEST",
            status_code=400,
            details={"field": "value"},
        )

        assert exc.message == "Test error"
        assert exc.error_code == "ERR_TEST"
        assert exc.status_code == 400
        assert exc.details == {"field": "value"}

    def test_authentication_error(self) -> None:
        """Test AuthenticationError defaults."""
        exc = AuthenticationError()

        assert exc.status_code == 401
        assert exc.error_code == ERR_AUTH_FAILED
        assert "Authentication required" in exc.message

    def test_authentication_error_custom(self) -> None:
        """Test AuthenticationError with custom values."""
        exc = AuthenticationError(message="Invalid token", error_code="ERR_TOKEN_EXPIRED")

        assert exc.status_code == 401
        assert exc.error_code == "ERR_TOKEN_EXPIRED"
        assert exc.message == "Invalid token"

    def test_authorization_error(self) -> None:
        """Test AuthorizationError."""
        exc = AuthorizationError()

        assert exc.status_code == 403
        assert exc.error_code == ERR_ADMIN_ONLY

    def test_validation_error(self) -> None:
        """Test ValidationError."""
        exc = DarsValidationError(
            message="Invalid grade",
            error_code="ERR_INVALID_GRADE",
            details={"provided": 10, "valid": [6, 7, 8]},
        )

        assert exc.status_code == 400
        assert exc.error_code == "ERR_INVALID_GRADE"
        assert exc.details["provided"] == 10

    def test_resource_not_found_error(self) -> None:
        """Test ResourceNotFoundError."""
        exc = ResourceNotFoundError(message="Student not found")

        assert exc.status_code == 404
        assert "not found" in exc.message.lower()

    def test_state_conflict_error(self) -> None:
        """Test StateConflictError."""
        exc = StateConflictError(message="Session already active")

        assert exc.status_code == 409
        assert "already active" in exc.message.lower()

    def test_external_service_error(self) -> None:
        """Test ExternalServiceError."""
        exc = ExternalServiceError(
            message="Claude API timeout",
            error_code=ERR_CLAUDE_TIMEOUT,
            details={"timeout_seconds": 3},
        )

        assert exc.status_code == 503
        assert exc.error_code == ERR_CLAUDE_TIMEOUT
        assert exc.details["timeout_seconds"] == 3


@pytest.mark.unit
class TestErrorHandlers:
    """Tests for error handler functions."""

    def test_map_status_to_error_type(self) -> None:
        """Test status code to error type mapping."""
        assert map_status_to_error_type(400) == "bad_request"
        assert map_status_to_error_type(401) == "unauthorized"
        assert map_status_to_error_type(403) == "forbidden"
        assert map_status_to_error_type(404) == "not_found"
        assert map_status_to_error_type(409) == "conflict"
        assert map_status_to_error_type(500) == "internal_error"
        assert map_status_to_error_type(503) == "service_unavailable"
        assert map_status_to_error_type(999) == "internal_error"  # Unknown

    def test_create_error_response(self) -> None:
        """Test error response creation."""
        response = create_error_response(
            status_code=404,
            message="Resource not found",
            error_code="ERR_NOT_FOUND",
            details={"resource": "student", "id": 123},
            request_id="test-request-id",
        )

        assert response.status_code == 404
        content = response.body.decode()
        assert "not_found" in content
        assert "Resource not found" in content
        assert "ERR_NOT_FOUND" in content
        assert "test-request-id" in content

    def test_dars_exception_handler(self) -> None:
        """Test DarsAPIException handler."""
        # Create mock request
        from unittest.mock import Mock

        request = Mock(spec=Request)
        request.state.request_id = "test-request-id"

        # Create exception
        exc = DarsAPIException(
            message="Test error",
            error_code="ERR_TEST",
            status_code=400,
        )

        # Handle exception
        response = dars_exception_handler(request, exc)

        assert response.status_code == 400
        content = response.body.decode()
        assert "Test error" in content
        assert "ERR_TEST" in content
        assert "test-request-id" in content

    def test_http_exception_handler(self) -> None:
        """Test HTTPException handler."""
        from unittest.mock import Mock

        request = Mock(spec=Request)
        request.state.request_id = "test-request-id"

        # Create HTTP exception
        exc = HTTPException(status_code=404, detail="Not found")

        # Handle exception
        response = http_exception_handler(request, exc)

        assert response.status_code == 404
        content = response.body.decode()
        assert "Not found" in content
        assert "test-request-id" in content


@pytest.mark.unit
class TestErrorCodes:
    """Tests to ensure all error codes are defined."""

    def test_auth_error_codes_exist(self) -> None:
        """Test authentication error codes are defined."""
        from src.errors.exceptions import (
            ERR_ADMIN_ONLY,
            ERR_AUTH_FAILED,
            ERR_AUTH_MISSING,
        )

        assert ERR_AUTH_FAILED == "ERR_AUTH_FAILED"
        assert ERR_AUTH_MISSING == "ERR_AUTH_MISSING"
        assert ERR_ADMIN_ONLY == "ERR_ADMIN_ONLY"

    def test_validation_error_codes_exist(self) -> None:
        """Test validation error codes are defined."""
        from src.errors.exceptions import (
            ERR_INVALID_ANSWER_FORMAT,
            ERR_INVALID_GRADE,
            ERR_INVALID_JSON,
            ERR_INVALID_LANGUAGE,
            ERR_INVALID_PARAM,
        )

        assert ERR_INVALID_JSON == "ERR_INVALID_JSON"
        assert ERR_INVALID_PARAM == "ERR_INVALID_PARAM"
        assert ERR_INVALID_GRADE == "ERR_INVALID_GRADE"
        assert ERR_INVALID_LANGUAGE == "ERR_INVALID_LANGUAGE"
        assert ERR_INVALID_ANSWER_FORMAT == "ERR_INVALID_ANSWER_FORMAT"

    def test_resource_error_codes_exist(self) -> None:
        """Test resource error codes are defined."""
        from src.errors.exceptions import (
            ERR_PROBLEM_NOT_FOUND,
            ERR_SESSION_EXPIRED,
            ERR_SESSION_NOT_FOUND,
            ERR_STUDENT_NOT_FOUND,
        )

        assert ERR_STUDENT_NOT_FOUND == "ERR_STUDENT_NOT_FOUND"
        assert ERR_PROBLEM_NOT_FOUND == "ERR_PROBLEM_NOT_FOUND"
        assert ERR_SESSION_NOT_FOUND == "ERR_SESSION_NOT_FOUND"
        assert ERR_SESSION_EXPIRED == "ERR_SESSION_EXPIRED"

    def test_external_service_error_codes_exist(self) -> None:
        """Test external service error codes are defined."""
        from src.errors.exceptions import (
            ERR_CLAUDE_API_FAILED,
            ERR_CLAUDE_TIMEOUT,
            ERR_DATABASE_ERROR,
            ERR_TELEGRAM_API_FAILED,
        )

        assert ERR_CLAUDE_API_FAILED == "ERR_CLAUDE_API_FAILED"
        assert ERR_CLAUDE_TIMEOUT == "ERR_CLAUDE_TIMEOUT"
        assert ERR_TELEGRAM_API_FAILED == "ERR_TELEGRAM_API_FAILED"
        assert ERR_DATABASE_ERROR == "ERR_DATABASE_ERROR"
