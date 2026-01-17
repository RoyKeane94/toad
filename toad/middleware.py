"""
Custom middleware for Content Security Policy (CSP) headers
"""
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class CSPMiddleware(MiddlewareMixin):
    """
    Middleware to add Content Security Policy headers.
    This helps protect against XSS attacks and other code injection attacks.
    """
    
    def process_response(self, request, response):
        """
        Add CSP headers to the response.
        """
        # Get S3 bucket URL for media-src if using S3
        media_src = "'self'"
        if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME') and settings.AWS_STORAGE_BUCKET_NAME:
            # Allow videos from S3 bucket
            s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')}.amazonaws.com"
            media_src = f"'self' {s3_url}"
        
        # Build form-action directive - allow same origin and Stripe checkout
        # 'self' should work, but explicitly allowing current origin as well
        current_origin = f"{request.scheme}://{request.get_host()}"
        form_action = f"'self' {current_origin} https://checkout.stripe.com"
        
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
            f"media-src {media_src} https:; "
            "connect-src 'self' "
            "https://plausible.io; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            f"form-action {form_action};"
        )
        
        # Add CSP header
        response['Content-Security-Policy'] = csp_policy
        
        return response

