#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    python - <<'PY'
import os
import socket
import time

host = os.environ.get('POSTGRES_HOST', 'db')
port = int(os.environ.get('POSTGRES_PORT', '5432'))
for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        if attempt == 59:
            raise SystemExit(f'PostgreSQL is unavailable at {host}:{port}')
        time.sleep(1)
PY

    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
fi

exec "$@"
