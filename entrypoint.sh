#!/bin/sh

# This script is the entrypoint for the web container.
# It ensures that database migrations are run before the web server starts.
# Using 'exec' allows gunicorn to properly receive signals for graceful shutdowns.

set -e

echo "Running Database Migrations..."
python3 manage.py migrate --noinput

echo "Starting Gunicorn Server..."
exec gunicorn toad.wsgi --log-file - 