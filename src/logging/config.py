"""Structured logging configuration with JSON output.

All logs are written to stdout in JSON format for easy parsing and aggregation.

Security (SEC-006):
- Sensitive data (API keys, tokens, passwords, admin IDs) are masked in all logs
- Prevents credential leakage through log files
- Applies to all log messages automatically
"""

import json
import logging
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings

# Sensitive field patterns to mask (SEC-006)
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "api-key",
    "token",
    "secret",
    "password",
    "passwd",
    "pwd",
    "admin_id",
    "admin-id",
    "x-admin-id",
    "authorization",
    "auth",
    "bearer",
    "telegram_bot_token",
    "telegram_secret_token",
    "anthropic_api_key",
    "x-telegram-bot-api-secret-token",
}


def sanitize_log_data(data: Any) -> Any:
    """Recursively sanitize sensitive data from log data.

    Security (SEC-006): Masks sensitive fields to prevent credential leakage.

    Sensitive fields include:
    - API keys (api_key, apikey, api-key)
    - Tokens (token, secret, bearer)
    - Passwords (password, passwd, pwd)
    - Admin IDs (admin_id, admin-id, x-admin-id)
    - Authorization headers (authorization, auth)

    Args:
        data: Data to sanitize (dict, list, str, or other type).

    Returns:
        Sanitized data with sensitive values masked as "***MASKED***".

    Example:
        >>> sanitize_log_data({"api_key": "secret123", "user": "john"})
        {"api_key": "***MASKED***", "user": "john"}
    """
    if isinstance(data, dict):
        return {
            key: "***MASKED***" if key.lower() in SENSITIVE_KEYS else sanitize_log_data(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    elif isinstance(data, str):
        # Check if string contains sensitive patterns
        lower_str = data.lower()
        for key in SENSITIVE_KEYS:
            if key in lower_str and ("=" in data or ":" in data):
                # Likely a key=value or key: value pattern
                return "***MASKED***"
        return data
    else:
        return data


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    Security (SEC-006): All log data is sanitized to remove sensitive information.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with sensitive data masked.

        Security (SEC-006): Automatically masks API keys, tokens, passwords,
        and admin IDs to prevent credential leakage.

        Args:
            record: Log record to format.

        Returns:
            JSON-formatted log string with sensitive data masked.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request_id if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add extra context if present
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # SEC-006: Sanitize all log data before outputting
        sanitized_data = sanitize_log_data(log_data)

        return json.dumps(sanitized_data)


class StructuredLogger:
    """Structured logger with JSON output and context support.

    Example:
        >>> logger = StructuredLogger(__name__)
        >>> logger.info("User logged in", user_id=123, request_id="abc")
        {"timestamp": "...", "level": "INFO", "message": "User logged in", ...}
    """

    def __init__(self, name: str) -> None:
        """Initialize the logger.

        Args:
            name: Logger name (typically __name__ of the module).
        """
        self.logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Log a message with extra context.

        Args:
            level: Log level (e.g., logging.INFO).
            message: Log message.
            **kwargs: Additional context to include in the log.
        """
        extra = {"extra": kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.CRITICAL, message, **kwargs)


def setup_logging() -> None:
    """Configure logging for the application.

    Sets up JSON-formatted logging to stdout with the configured log level.
    """
    settings = get_settings()

    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        StructuredLogger instance.
    """
    return StructuredLogger(name)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request_id to each request.

    The request_id is:
    - Generated for each incoming request
    - Stored in request.state for access in route handlers
    - Included in all logs for that request
    - Returned in error responses
    """

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process the request and add request_id.

        Args:
            request: Incoming request.
            call_next: Next middleware or route handler.

        Returns:
            Response from the next handler.
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request_id to log context
        logger = get_logger(__name__)
        logger.info(
            f"{request.method} {request.url.path}",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # Process request
        response = await call_next(request)

        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def request_id_middleware(app: Any) -> None:
    """Add RequestIDMiddleware to the FastAPI app.

    Args:
        app: FastAPI application instance.
    """
    app.add_middleware(RequestIDMiddleware)
