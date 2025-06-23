release: export RAILWAY_DEBUG_ENVIRONMENT=1 && npm run build:all && python3 manage.py collectstatic --no-input --clear && python3 manage.py migrate
web: gunicorn toad.wsgi --log-file -
