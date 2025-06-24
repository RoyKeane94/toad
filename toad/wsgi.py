"""
WSGI config for toad project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toad.settings')

# Get the standard Django application
application = get_wsgi_application()

# Wrap the application with WhiteNoise to serve static files from STATIC_ROOT.
# This is the crucial step that makes WhiteNoise aware of your collected files.
application = WhiteNoise(application)