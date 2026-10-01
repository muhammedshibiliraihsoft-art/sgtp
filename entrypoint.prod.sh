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

bootstrap_enabled="$(printf '%s' "${STAGING_SMOKE_BOOTSTRAP_ENABLED:-false}" | tr '[:upper:]' '[:lower:]')"
rotation_enabled="$(printf '%s' "${STAGING_SMOKE_ROTATE_CREDENTIALS_ENABLED:-false}" | tr '[:upper:]' '[:lower:]')"
if [ "$bootstrap_enabled" = "true" ] && [ "$rotation_enabled" = "true" ]; then
  echo "Staging smoke bootstrap and credential rotation cannot be enabled together." >&2
  exit 1
fi

# A one-time, explicitly enabled staging fixture hook. The Django command
# independently enforces environment, database, secret, and confirmation guards.
case "${STAGING_SMOKE_BOOTSTRAP_ENABLED:-false}" in
  true|TRUE|True)
    if [ "${DJANGO_ENV:-}" != "staging" ]; then
      echo "Staging smoke bootstrap cannot run outside DJANGO_ENV=staging." >&2
      exit 1
    fi
    echo "[staging] Creating guarded synthetic smoke-test fixture..."
    python manage.py bootstrap_staging_smoke --confirm-staging-bootstrap
    ;;
  false|FALSE|False|'')
    ;;
  *)
    echo "Invalid STAGING_SMOKE_BOOTSTRAP_ENABLED value; expected true or false." >&2
    exit 1
    ;;
esac

# A separately gated one-time password rotation for the existing synthetic
# fixture. Both this entrypoint and the Django command enforce staging scope.
case "${STAGING_SMOKE_ROTATE_CREDENTIALS_ENABLED:-false}" in
  true|TRUE|True)
    if [ "${DJANGO_ENV:-}" != "staging" ]; then
      echo "Staging smoke credential rotation cannot run outside DJANGO_ENV=staging." >&2
      exit 1
    fi
    echo "[staging] Rotating credentials for the existing synthetic fixture..."
    python manage.py rotate_staging_smoke_credentials --confirm-staging-credential-rotation
    ;;
  false|FALSE|False|'')
    ;;
  *)
    echo "Invalid STAGING_SMOKE_ROTATE_CREDENTIALS_ENABLED value; expected true or false." >&2
    exit 1
    ;;
esac

# A separate one-time bootstrap for the real staging Main Supplier Admin.
# Its Django command independently verifies environment and database scope.
case "${STAGING_MAIN_ADMIN_BOOTSTRAP_ENABLED:-false}" in
  true|TRUE|True)
    if [ "${DJANGO_ENV:-}" != "staging" ]; then
      echo "Main Admin bootstrap cannot run outside DJANGO_ENV=staging." >&2
      exit 1
    fi
    echo "[staging] Creating the configured Main Supplier Admin if absent..."
    python manage.py bootstrap_staging_main_admin --confirm-staging-main-admin-bootstrap
    ;;
  false|FALSE|False|'')
    ;;
  *)
    echo "Invalid STAGING_MAIN_ADMIN_BOOTSTRAP_ENABLED value; expected true or false." >&2
    exit 1
    ;;
esac

# Start Gunicorn
echo "[${DJANGO_ENV:-unknown}] Starting Gunicorn..."
exec "$@"
