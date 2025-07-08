import logging
from django.shortcuts import render, redirect
from django.http import Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from ..specific_views_functions.error_views_functions import (
    handle_404_error,
    handle_500_error,
    handle_403_error,
    handle_test_error_request
)

# Set up logging
logger = logging.getLogger(__name__)

# Error handling views
def handler404(request, exception):
    """Custom 404 error handler"""
    return handle_404_error(request, exception)

def handler500(request):
    """Custom 500 error handler"""
    return handle_500_error(request)

def handler403(request, exception):
    """Custom 403 error handler"""
    return handle_403_error(request, exception)

# Test error views (only for development)
def test_404(request):
    """Test view to trigger 404 error"""
    return handle_test_error_request('404')

def test_500(request):
    """Test view to trigger 500 error"""
    return handle_test_error_request('500')

def test_403(request):
    """Test view to trigger 403 error"""
    return handle_test_error_request('403')
