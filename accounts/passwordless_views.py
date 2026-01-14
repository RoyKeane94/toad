"""
Passwordless Login Views
========================
Views for passwordless authentication using email codes.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.cache import cache
import logging

from .passwordless_forms import RequestLoginCodeForm, VerifyLoginCodeForm
from .passwordless_models import LoginCode
from .models import User
from .email_utils import send_passwordless_login_code

logger = logging.getLogger(__name__)


class RequestLoginCodeView(FormView):
    """
    View for requesting a login code via email.
    """
    template_name = 'accounts/pages/login/passwordless_request.html'
    form_class = RequestLoginCodeForm
    success_url = reverse_lazy('accounts:passwordless_verify')
    
    def form_valid(self, form):
        """Generate and send login code."""
        email = form.cleaned_data['email']
        ip_address = self.get_client_ip()
        
        # Check rate limiting
        allowed, remaining = LoginCode.check_rate_limit(email, ip_address)
        if not allowed:
            minutes = remaining // 60
            seconds = remaining % 60
            messages.error(
                self.request,
                f'Too many code requests. Please wait {minutes}m {seconds}s before requesting another code.'
            )
            return self.form_invalid(form)
        
        # Get or create user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists - show same success message
            # This prevents email enumeration attacks
            messages.success(
                self.request,
                'If an account with that email exists, a login code has been sent. '
                'Please check your email and enter the code below.'
            )
            # Store email in session for verification step
            self.request.session['passwordless_email'] = email
            return redirect('accounts:passwordless_verify')
        
        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > timezone.now():
            messages.error(
                self.request,
                'This account is temporarily locked. Please try again later or contact support.'
            )
            return self.form_invalid(form)
        
        # Generate login code
        try:
            login_code, plain_code = LoginCode.create_for_user(
                user=user,
                ip_address=ip_address,
                code_length=6,
                expiry_minutes=10
            )
            
            # Record rate limit
            LoginCode.record_code_request(email, ip_address)
            
            # Send email with code
            email_sent = send_passwordless_login_code(user, plain_code, self.request)
            
            if email_sent:
                # Store email in session for verification step
                self.request.session['passwordless_email'] = email
                messages.success(
                    self.request,
                    f'Login code sent to {email}. Please check your email and enter the code below. '
                    'The code will expire in 10 minutes.'
                )
                logger.info(f"Login code sent to {email}")
            else:
                messages.error(
                    self.request,
                    'Failed to send login code. Please try again or use password login.'
                )
                logger.error(f"Failed to send login code to {email}")
                return self.form_invalid(form)
                
        except Exception as e:
            logger.error(f"Error generating login code for {email}: {e}")
            messages.error(
                self.request,
                'An error occurred. Please try again or use password login.'
            )
            return self.form_invalid(form)
        
        return redirect('accounts:passwordless_verify')
    
    def get_client_ip(self):
        """Get client IP address for rate limiting."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class VerifyLoginCodeView(FormView):
    """
    View for verifying the login code and logging in the user.
    """
    template_name = 'accounts/pages/login/passwordless_verify.html'
    form_class = VerifyLoginCodeForm
    success_url = reverse_lazy('pages:project_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Check if email is in session."""
        if not request.session.get('passwordless_email'):
            messages.warning(request, 'Please request a login code first.')
            return redirect('accounts:passwordless_request')
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Pre-populate email from session."""
        return {
            'email': self.request.session.get('passwordless_email')
        }
    
    def get_context_data(self, **kwargs):
        """Add email to context."""
        context = super().get_context_data(**kwargs)
        context['email'] = self.request.session.get('passwordless_email')
        return context
    
    def form_valid(self, form):
        """Verify code and log in user."""
        email = form.cleaned_data['email']
        code = form.cleaned_data['code']
        
        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Clear session and show error
            self.request.session.pop('passwordless_email', None)
            messages.error(
                self.request,
                'Invalid code or email. Please request a new code.'
            )
            return redirect('accounts:passwordless_request')
        
        # Verify code
        login_code = LoginCode.get_valid_code(user, code)
        
        if not login_code:
            # Code is invalid or expired
            messages.error(
                self.request,
                'Invalid or expired code. Please request a new code.'
            )
            logger.warning(f"Failed login code attempt for {email}")
            return self.form_invalid(form)
        
        # Check if email is verified (allow Personal plan users)
        if not user.email_verified and user.tier != 'personal':
            messages.error(
                self.request,
                'Please verify your email address before logging in. Check your inbox for the verification link.'
            )
            # Clear session
            self.request.session.pop('passwordless_email', None)
            return redirect('accounts:login')
        
        # Log the user in
        login(self.request, user)
        
        # Clear session
        self.request.session.pop('passwordless_email', None)
        
        # Log successful login
        logger.info(f"Passwordless login successful for {email}")
        
        messages.success(
            self.request,
            f'Welcome back, {user.get_short_name()}!'
        )
        
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        """Handle invalid form."""
        messages.error(self.request, 'Please enter a valid 6-digit code.')
        return super().form_invalid(form)

