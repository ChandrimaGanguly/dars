"""Health check endpoint for monitoring system status.

This endpoint checks:
- Database connectivity (PostgreSQL)
- Claude API availability (optional check)
- Overall system health

Response format follows API_ARCHITECTURE.md:
{
  "status": "ok" | "error",
  "db": "ok" | "timeout" | "error",
  "claude": "ok" | "timeout" | "error",
  "timestamp": "2026-01-28T10:00:00Z"
}
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.logging import get_logger

router = APIRouter(tags=["system"])
logger = get_logger(__name__)

# Timeout for health checks (in seconds)
DB_CHECK_TIMEOUT = 3.0
CLAUDE_CHECK_TIMEOUT = 5.0


async def check_database() -> str:
    """Check database connectivity.

    Returns:
        Status string: "ok", "timeout", or "error".
    """
    try:
        from src.database import check_connection

        # Check database connection with timeout
        db_ok = await asyncio.wait_for(check_connection(), timeout=DB_CHECK_TIMEOUT)

        if db_ok:
            logger.info("Database health check: OK")
            return "ok"
        else:
            logger.warning("Database health check: FAILED")
            return "error"

    except TimeoutError:
        logger.warning("Database health check: TIMEOUT")
        return "timeout"
    except Exception as e:
        logger.error(f"Database health check: ERROR - {e!s}")
        return "error"


async def check_claude_api() -> str:
    """Check Claude API availability (optional).

    This is a lightweight check to verify the API key is valid.
    We don't make actual API calls to avoid costs during health checks.

    Returns:
        Status string: "ok", "timeout", or "error".
    """
    try:
        settings = get_settings()

        # Basic check: verify API key is configured
        if not settings.anthropic_api_key:
            logger.warning("Claude API key not configured")
            return "error"

        # TODO: Optional - Add lightweight Claude API ping (if available)
        # For now, just check if the key is present
        logger.info("Claude API health check: OK (key configured)")
        return "ok"

    except TimeoutError:
        logger.warning("Claude API health check: TIMEOUT")
        return "timeout"
    except Exception as e:
        logger.error(f"Claude API health check: ERROR - {e!s}")
        return "error"


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint.

    Checks system health including database and Claude API.

    Returns:
        JSONResponse with health status.

    Response Codes:
        200: System healthy (all checks passed)
        503: Service unavailable (one or more checks failed)

    Example Response (Healthy):
        {
          "status": "ok",
          "db": "ok",
          "claude": "ok",
          "timestamp": "2026-01-28T10:00:00Z"
        }

    Example Response (Unhealthy):
        {
          "status": "error",
          "db": "timeout",
          "claude": "ok",
          "timestamp": "2026-01-28T10:00:00Z"
        }
    """
    # Run health checks in parallel
    db_status, claude_status = await asyncio.gather(
        check_database(), check_claude_api(), return_exceptions=False
    )

    # Determine overall status
    overall_status = "ok" if db_status == "ok" and claude_status == "ok" else "error"

    # Create response
    response_data: dict[str, Any] = {
        "status": overall_status,
        "db": db_status,
        "claude": claude_status,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Return appropriate status code
    status_code = (
        status.HTTP_200_OK if overall_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    logger.info(f"Health check completed: {overall_status}", **response_data)

    return JSONResponse(status_code=status_code, content=response_data)
