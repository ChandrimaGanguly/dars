#!/bin/sh
# Diagnose private networking
echo "=== Network diagnostics ==="
python3 -c "
import socket

# DNS resolution
for host in ['postgres.railway.internal', 'gondola.proxy.rlwy.net']:
    try:
        results = socket.getaddrinfo(host, 5432, type=socket.SOCK_STREAM)
        print(f'DNS {host}: {[(r[0].name, r[4]) for r in results]}')
    except Exception as e:
        print(f'DNS {host}: FAILED - {e}')

# Quick TCP connectivity (2s timeout to stay within healthcheck window)
tests = [
    ('10.205.136.78', 5432, socket.AF_INET),
    ('postgres.railway.internal', 5432, socket.AF_INET6),
    ('postgres.railway.internal', 5432, socket.AF_INET),
    ('gondola.proxy.rlwy.net', 21425, socket.AF_INET),
]
for host, port, family in tests:
    s = socket.socket(family, socket.SOCK_STREAM)
    s.settimeout(2)
    label = f'TCP {socket.AddressFamily(family).name} {host}:{port}'
    try:
        s.connect((host, port))
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
