from django.shortcuts import render, redirect
from django.http import Http404
from django.conf import settings
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

# Error Logging Helpers

def log_error_event(error_type, request, additional_info=None):
    """Log error events with consistent formatting"""
    user_info = request.user.username if request.user.is_authenticated else 'Anonymous'
    log_message = f"{error_type} error: {request.path} - User: {user_info}"
    
    if additional_info:
        log_message += f" - {additional_info}"
    
    if error_type == '404':
        logger.warning(log_message)
    elif error_type == '403':
        logger.warning(log_message)
    elif error_type == '500':
        logger.error(log_message)
    else:
        logger.error(log_message)

def get_error_context(error_type, request, exception=None):
    """Get common context for error pages"""
    context = {
        'error_type': error_type,
        'is_authenticated': request.user.is_authenticated,
        'debug_mode': settings.DEBUG,
    }
    
    if exception and settings.DEBUG:
        context['exception_message'] = str(exception)
    
    return context

# Error Handler Helpers

def handle_404_error(request, exception):
    """Handle 404 errors with logging and rendering"""
    log_error_event('404', request, f"Exception: {str(exception)}")
    context = get_error_context('404', request, exception)
    return render(request, 'pages/errors/404.html', context, status=404)

def handle_500_error(request):
    """Handle 500 errors with logging and rendering"""
    log_error_event('500', request)
    context = get_error_context('500', request)
    return render(request, 'pages/errors/500.html', context, status=500)

def handle_403_error(request, exception):
    """Handle 403 errors with logging and rendering"""
    log_error_event('403', request, f"Exception: {str(exception)}")
    context = get_error_context('403', request, exception)
    return render(request, 'pages/errors/403.html', context, status=403)

# Test Error Helpers

def create_test_error(error_type, message=None):
    """Create test errors for development"""
    if not settings.DEBUG:
        return False
    
    default_messages = {
        '404': "This is a test 404 error",
        '500': "This is a test 500 error", 
        '403': "This is a test 403 error"
    }
    
    error_message = message or default_messages.get(error_type, "This is a test error")
    
    if error_type == '404':
        raise Http404(error_message)
    elif error_type == '500':
        raise Exception(error_message)
    elif error_type == '403':
        raise PermissionDenied(error_message)
    else:
        raise Exception(error_message)

def handle_test_error_request(error_type):
    """Handle test error requests with proper fallback"""
    if settings.DEBUG:
        create_test_error(error_type)
    return redirect('pages:home')

# Error Response Helpers

def get_safe_redirect_response():
    """Get a safe redirect response for error handling"""
    return redirect('pages:home')

def is_ajax_request(request):
    """Check if request is AJAX/HTMX"""
    return (
        request.headers.get('HX-Request') or 
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )
