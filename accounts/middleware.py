from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class EmailVerificationMiddleware:
    """
    Middleware to ensure users have verified their email before accessing the site.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user is authenticated but email is not verified
        if (request.user.is_authenticated and 
            not request.user.email_verified and
            not request.path.startswith('/accounts/') and  # Allow access to account pages
            not request.path.startswith('/admin/') and     # Allow admin access
            request.path != '/'):                          # Allow home page
            
            messages.warning(request, 'Please verify your email address to access all features.')
            return redirect('accounts:account_settings')
        
        response = self.get_response(request)
        return response 