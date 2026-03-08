#!/bin/sh
for i in 1 2 3; do
  echo "Alembic migration attempt $i..."
  output=$(timeout 20 /opt/venv/bin/alembic upgrade head 2>&1)
  exit_code=$?
  echo "$output"
  echo "Alembic exit code: $exit_code"
  if [ $exit_code -eq 0 ]; then
    echo "Alembic migration succeeded"
    break
  fi
  echo "Attempt $i failed, waiting 5s..."
  sleep 5
done

exec /opt/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
