"""
URL configuration for toad project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponse
from django.views.generic import RedirectView
import os

# Favicon view
def favicon_view(request):
    return serve(request, 'img/favicon.svg', document_root=settings.STATIC_ROOT)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('accounts/', include('accounts.urls')),
    path('lilypad/', include('CRM.urls')),
    path('favicon.svg', favicon_view, name='favicon'),
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.svg', permanent=True)),
]

# Custom error handlers
handler404 = 'pages.views.handler404'
handler500 = 'pages.views.handler500'
handler403 = 'CRM.views.crm_403_error'

# Serve static files when DEBUG = False (for development/testing)
# This manually serves static files using Django's serve view
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    ]
else:
    # Standard static file serving when DEBUG = True
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Serve media files in development
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)