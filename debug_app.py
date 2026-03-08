"""Debug app to identify Railway lifespan startup failure."""
import os
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

_startup_error: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _startup_error
    try:
        from src.scheduler import start_scheduler
        start_scheduler()
        _startup_error = None
    except Exception:
        _startup_error = traceback.format_exc()
    yield
    try:
        from src.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "port": os.environ.get("PORT", "not set"),
        "scheduler_error": _startup_error,
    }
