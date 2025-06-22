release: export RAILWAY_DEBUG_ENVIRONMENT=1 && python3 manage.py collectstatic --no-input && python3 manage.py migrate
web: gunicorn toad.wsgi --log-file -
