"""Common Pydantic schemas shared across endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    error_code: str | None = Field(None, description="Machine-readable error code")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: str | None = Field(None, description="Correlation ID for debugging")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall system status", examples=["ok", "error"])
    db: str | None = Field(
        None, description="Database connection status", examples=["ok", "timeout", "error"]
    )
    claude: str | None = Field(
        None, description="Claude API status", examples=["ok", "timeout", "error"]
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
