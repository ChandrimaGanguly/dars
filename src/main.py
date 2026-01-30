"""Dars AI Tutoring Platform - FastAPI Application.

This is the main FastAPI application entry point. It configures the app,
registers all routers, and sets up middleware.
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config import get_settings
from src.database import check_connection, get_engine
from src.errors.handlers import register_exception_handlers
from src.logging import get_logger
from src.routes import admin, health, practice, streak, student, webhook

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Handles startup and shutdown tasks:
    - Startup: Initialize database connections, validate config
    - Shutdown: Close database connections gracefully

    Args:
        app: FastAPI application instance.

    Yields:
        None during application runtime.
    """
    # STARTUP
    logger.info("Dars API starting up...")

    # Validate environment variables
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log level: {settings.log_level}")

    # Check database connection
    db_connected = await check_connection()
    if db_connected:
        logger.info("Database connection: OK")
    else:
        logger.warning("Database connection: FAILED (will retry on first request)")

    # Validate API keys are configured
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured")
    if not settings.anthropic_api_key:
        logger.warning("Anthropic API key not configured")

    logger.info("Dars API startup complete")

    yield

    # SHUTDOWN
    logger.info("Dars API shutting down...")

    # Close database connections
    engine = get_engine()
    await engine.dispose()
    logger.info("Database connections closed")

    logger.info("Dars API shutdown complete")


# Create FastAPI application instance
app = FastAPI(
    title="Dars AI Tutoring Platform API",
    version="1.0.0",
    description="""
    REST API for Dars AI tutoring backend.

    ## Features

    * **Telegram Integration**: Webhook endpoint for bot updates
    * **Practice Sessions**: Daily 5-problem practice with adaptive difficulty
    * **Socratic Hints**: AI-powered guidance without revealing answers
    * **Streak Tracking**: Gamification with daily streaks and milestones
    * **Admin Dashboard**: System statistics, cost tracking, student management

    ## Authentication

    * Telegram webhook: Bearer token authentication
    * Student endpoints: X-Student-ID header (Telegram ID)
    * Admin endpoints: X-Admin-ID header (Telegram ID)

    ## Rate Limiting (SEC-005)

    * Global: 100 requests/minute per IP
    * Hint endpoint: 10 requests/day per student
    """,
    contact={
        "name": "Dars Team",
        "email": "team@dars.ai",
    },
    license_info={
        "name": "MIT",
    },
    servers=[
        {
            "url": "https://dars.railway.app",
            "description": "Production server",
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development server",
        },
    ],
    lifespan=lifespan,
)


# Configure rate limiter (SEC-005: Prevent DOS attacks)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

logger.info("Rate limiting enabled: 100 requests/minute per IP")


# Request ID middleware - MUST be first
@app.middleware("http")
async def add_request_id(request: Request, call_next):  # type: ignore
    """Add unique request ID to each request.

    The request ID is:
    - Stored in request.state for access by handlers
    - Added to response headers for client tracking
    - Included in all log messages for tracing

    Args:
        request: FastAPI request object.
        call_next: Next middleware or route handler.

    Returns:
        Response with X-Request-ID header.
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Configure CORS middleware (SEC-001: Hardened by Noor)
# Security: Restrict CORS to prevent unauthorized cross-origin requests
settings = get_settings()

# Allowed origins (only production and development)
allowed_origins = [
    "https://dars.railway.app",  # Production Railway deployment
    "http://localhost:3000",  # Local development (admin dashboard)
    "http://localhost:8000",  # Local development (API testing)
]

# If in development mode, also allow 127.0.0.1
if settings.environment == "development":
    allowed_origins.extend(
        [
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # SEC-001: Restricted to specific domains
    allow_credentials=True,  # Allow cookies/auth headers for same-origin
    allow_methods=["GET", "POST", "PATCH"],  # SEC-001: Only required methods
    allow_headers=[  # SEC-001: Only required headers
        "Content-Type",
        "Authorization",
        "X-Student-ID",
        "X-Admin-ID",
        "X-Request-ID",
        "X-Telegram-Bot-Api-Secret-Token",
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
)


# Register error handlers
register_exception_handlers(app)


# Register routers
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(practice.router)
app.include_router(streak.router)
app.include_router(student.router)
app.include_router(admin.router)


# Root endpoint
@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Root endpoint returning API information.

    Returns:
        dict with API name, version, and documentation links.
    """
    return {
        "name": "Dars AI Tutoring Platform API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }
