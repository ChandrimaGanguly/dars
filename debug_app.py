"""Minimal debug app to test Railway deployment."""
import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root() -> dict:
    return {"status": "ok", "port": os.environ.get("PORT", "not set")}
