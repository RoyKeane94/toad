release: python manage.py collectstatic --noinput && python manage.py migrate
web: gunicorn toad.wsgi --log-file -