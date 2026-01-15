"""
Custom middleware for Content Security Policy (CSP) headers
"""
from django.utils.deprecation import MiddlewareMixin


class CSPMiddleware(MiddlewareMixin):
    """
    Middleware to add Content Security Policy headers.
    This helps protect against XSS attacks and other code injection attacks.
    """
    
    def process_response(self, request, response):
        """
        Add CSP headers to the response.
        """
        # Build CSP policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net "
            "https://cdnjs.cloudflare.com "
            "https://plausible.io; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdnjs.cloudflare.com "
            "https://fonts.googleapis.com; "
            "font-src 'self' "
            "https://cdnjs.cloudflare.com "
            "https://fonts.gstatic.com "
            "data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self' "
            "https://plausible.io; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Add CSP header
        response['Content-Security-Policy'] = csp_policy
        
        return response

