#!/bin/sh
# Retry alembic up to 3 times with backoff (DB may not be ready at container start)
for i in 1 2 3; do
  echo "Alembic migration attempt $i..."
  timeout 20 /opt/venv/bin/alembic upgrade head && break
  echo "Attempt $i failed, waiting 5s..."
  sleep 5
done

exec /opt/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
