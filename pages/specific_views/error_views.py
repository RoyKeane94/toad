import logging

# Set up logging
logger = logging.getLogger(__name__)

# Error handling views
def handler404(request, exception):
    """Custom 404 error handler"""
    logger.warning(f"404 error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}")
    return render(request, 'pages/errors/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    logger.error(f"500 error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}")
    return render(request, 'pages/errors/500.html', status=500)

def handler403(request, exception):
    """Custom 403 error handler"""
    logger.warning(f"403 error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}")
    return render(request, 'pages/errors/403.html', status=403)

# Test error views (only for development)
def test_404(request):
    """Test view to trigger 404 error"""
    if settings.DEBUG:
        raise Http404("This is a test 404 error")
    return redirect('pages:home')

def test_500(request):
    """Test view to trigger 500 error"""
    if settings.DEBUG:
        raise Exception("This is a test 500 error")
    return redirect('pages:home')

def test_403(request):
    """Test view to trigger 403 error"""
    if settings.DEBUG:
        raise PermissionDenied("This is a test 403 error")
    return redirect('pages:home')
