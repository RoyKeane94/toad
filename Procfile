release: npm run build:production && python manage.py migrate
web: gunicorn toad.wsgi --log-file -