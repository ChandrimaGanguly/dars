"""Dars AI Tutoring Platform - FastAPI Application.

This is the main FastAPI application entry point. It configures the app,
registers all routers, and sets up middleware.
"""

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.routes import admin, health, practice, streak, student, webhook

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
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(practice.router)
app.include_router(streak.router)
app.include_router(student.router)
app.include_router(admin.router)


# Startup event handler
@app.on_event("startup")
async def startup_event() -> None:
    """Execute tasks on application startup.

    - Initialize database connections
    - Set up logging
    - Validate environment variables
    - Initialize caches
    """
    # TODO: Implement startup logic
    # - Connect to PostgreSQL
    # - Initialize Redis cache
    # - Validate required environment variables
    # - Set up structured logging
    print(f"[{datetime.utcnow().isoformat()}] Dars API starting up...")


# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Execute cleanup tasks on application shutdown.

    - Close database connections
    - Flush logs
    - Save cache state
    """
    # TODO: Implement shutdown logic
    # - Close database connections gracefully
    # - Flush pending logs
    print(f"[{datetime.utcnow().isoformat()}] Dars API shutting down...")


# Root endpoint
@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Root endpoint returning API information.

    Returns:
        dict with API name and version.
    """
    return {
        "name": "Dars AI Tutoring Platform API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: object, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions globally.

    Args:
        request: The request object that caused the exception.
        exc: The exception that was raised.

    Returns:
        JSONResponse with error details.
    """
    # TODO: Implement proper error logging
    # - Log exception with context
    # - Generate request_id for tracing
    # - Send alert for critical errors

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Something went wrong processing your request",
            "error_code": "ERR_INTERNAL",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
