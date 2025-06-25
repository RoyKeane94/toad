release: python3 manage.py migrate --verbosity=2
web: python3 manage.py migrate && gunicorn toad.wsgi --bind 0.0.0.0:$PORT --log-file -