#!/bin/sh
/opt/venv/bin/alembic upgrade head || echo "Alembic migration failed, continuing..."
exec /opt/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
