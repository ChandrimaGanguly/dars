"""Structured logging for the Dars API.

This module provides:
- JSON-formatted logging
- Request ID tracking
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log to stdout (captured by Railway/Render)
"""

from src.logging.config import (
    StructuredLogger,
    get_logger,
    request_id_middleware,
    setup_logging,
)

__all__ = [
    "StructuredLogger",
    "get_logger",
    "request_id_middleware",
    "setup_logging",
]
