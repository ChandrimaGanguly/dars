#!/bin/sh
timeout 15 /opt/venv/bin/alembic upgrade head || echo "Alembic migration failed or timed out, continuing..."
exec /opt/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
