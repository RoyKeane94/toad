release: python manage.py tailwind build && python manage.py collectstatic --no-input && python manage.py migrate
web: gunicorn toad.wsgi --log-file -
