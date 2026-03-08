#!/bin/sh
# Diagnose private networking
echo "=== Network diagnostics ==="
python3 -c "
import os, socket
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', '')
parsed = urlparse(db_url)
db_host = parsed.hostname or 'unknown'
db_port = parsed.port or 5432

print(f'DATABASE_URL host: {db_host}:{db_port}')

# DNS resolution
for host in [db_host]:
    try:
        results = socket.getaddrinfo(host, db_port, type=socket.SOCK_STREAM)
        print(f'DNS {host}: {[(r[0].name, r[4]) for r in results]}')
    except Exception as e:
        print(f'DNS {host}: FAILED - {e}')

# Quick TCP connectivity (2s timeout)
for family in [socket.AF_INET, socket.AF_INET6]:
    s = socket.socket(family, socket.SOCK_STREAM)
    s.settimeout(2)
    label = f'TCP {socket.AddressFamily(family).name} {db_host}:{db_port}'
    try:
        s.connect((db_host, db_port))
        s.close()
        print(f'{label}: CONNECTED')
    except socket.timeout:
        print(f'{label}: TIMEOUT')
    except ConnectionRefusedError:
        print(f'{label}: REFUSED')
    except OSError as e:
        print(f'{label}: {e}')
    finally:
        s.close()
"
echo "==========================="

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
