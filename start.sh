#!/bin/sh
# Log which DB host alembic will use (strip password for safety)
db_url="${DATABASE_PUBLIC_URL:-${DATABASE_URL:-unset}}"
db_host=$(echo "$db_url" | python3 -c "import sys,urllib.parse; u=urllib.parse.urlparse(sys.stdin.read().strip()); print(u.hostname, u.port)" 2>/dev/null)
echo "Alembic target: $db_host"

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
