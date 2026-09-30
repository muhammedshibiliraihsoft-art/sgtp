#!/bin/bash
set -e

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_WAIT_TIMEOUT_SECONDS="${DB_WAIT_TIMEOUT_SECONDS:-60}"

case "$DB_WAIT_TIMEOUT_SECONDS" in
  ''|*[!0-9]*)
    echo "Invalid DB_WAIT_TIMEOUT_SECONDS; expected a positive integer." >&2
    exit 1
    ;;
esac
if [ "$DB_WAIT_TIMEOUT_SECONDS" -lt 1 ]; then
  echo "Invalid DB_WAIT_TIMEOUT_SECONDS; expected a positive integer." >&2
  exit 1
fi

echo "[${DJANGO_ENV:-unknown}] Waiting up to ${DB_WAIT_TIMEOUT_SECONDS}s for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
elapsed=0
until nc -z -w 2 "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$DB_WAIT_TIMEOUT_SECONDS" ]; then
    echo "PostgreSQL was not reachable at ${DB_HOST}:${DB_PORT} before the startup timeout." >&2
    exit 1
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
echo "[${DJANGO_ENV:-unknown}] PostgreSQL is reachable."

# Run migrations
echo "[${DJANGO_ENV:-unknown}] Applying committed migrations..."
python manage.py migrate --noinput

# Collect static files
echo "[${DJANGO_ENV:-unknown}] Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "[${DJANGO_ENV:-unknown}] Starting Gunicorn..."
exec "$@"
