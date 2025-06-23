release: npm ci && npm run build:css && npm run build:js && python3 manage.py collectstatic --no-input --clear && python3 manage.py migrate
web: gunicorn toad.wsgi --log-file -
