release: python3 manage.py migrate --verbosity=2
web: gunicorn toad.wsgi --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload --log-file -