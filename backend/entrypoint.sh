#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q; do
  sleep 1
done
echo "PostgreSQL is up."

python manage.py migrate --noinput
python manage.py seed_initial_data
python manage.py collectstatic --noinput

exec "$@"
