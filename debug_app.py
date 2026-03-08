"""Debug app to identify Railway startup failure."""
import os
import traceback

from fastapi import FastAPI

app = FastAPI()

# Try importing src.main and capture any error
_import_error: str | None = None
try:
    import src.main as _main_module  # noqa: F401
    _import_result = "OK"
except Exception as e:
    _import_error = traceback.format_exc()
    _import_result = f"FAILED: {e}"


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "port": os.environ.get("PORT", "not set"),
        "src_main_import": _import_result,
        "error": _import_error,
    }
