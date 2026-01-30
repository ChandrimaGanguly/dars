"""Structured logging configuration."""

import logging
import sys
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Set level
        logger.setLevel(logging.INFO)

        # Create console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Create formatter (JSON-like for structured logging)
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    return logger


# Example usage functions for different log levels
def log_info(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log info message with additional context."""
    logger.info(message, extra=kwargs)


def log_error(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log error message with additional context."""
    logger.error(message, extra=kwargs)


def log_warning(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log warning message with additional context."""
    logger.warning(message, extra=kwargs)
