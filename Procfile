release: python3 manage.py migrate
web: python3 manage.py migrate && gunicorn toad.wsgi --log-file -