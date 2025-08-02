from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.http import Http404
from .models import User
from .forms import (
    EmailAuthenticationForm, 
    CustomUserCreationForm, 
    ProfileUpdateForm, 
    CustomPasswordChangeForm, 
    AccountDeletionForm,
    ForgotPasswordForm
)
from .email_utils import send_verification_email, send_password_reset_email

# Create your views here.

class LoginView(FormView):
    """
    Custom login view using email authentication
    """
    template_name = 'accounts/pages/login.html'
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy('pages:project_list')  # Updated to project list
    
    def get_context_data(self, **kwargs):
        """Add context for verification messages"""
        context = super().get_context_data(**kwargs)
        
        # Check if user just registered and needs verification
        if self.request.session.get('show_verification_message'):
            context['show_verification_message'] = True
            # Remove the flag so it only shows once
            del self.request.session['show_verification_message']
        
        return context
    
    def form_valid(self, form):
        """Login the user and redirect to success URL"""
        user = form.get_user()
        
        # Check if email is verified
        if not user.email_verified:
            messages.error(
                self.request, 
                'Please verify your email address before logging in. Check your inbox and spam folder for the verification link. If you haven\'t received it, you can request a new verification email below.'
            )
            return redirect('accounts:login')
        
        login(self.request, user)
        messages.success(self.request, f'Welcome back, {user.get_short_name()}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from login page"""
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

class RegisterView(FormView):
    """
    Custom registration view using email authentication
    """
    template_name = 'accounts/pages/register.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and send verification email"""
        user = form.save()
        
        # Log registration attempt
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"New user registration: {user.email} ({user.get_short_name()})")
        
        # Add session flag immediately for better UX
        self.request.session['show_verification_message'] = True
        
        # Send verification email asynchronously to improve performance
        try:
            import threading
            def send_email_async():
                try:
                    email_sent = send_verification_email(user, self.request)
                    logger.info(f"Verification email sent: {email_sent} for {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send verification email to {user.email}: {e}")
            
            # Start email sending in background thread
            email_thread = threading.Thread(target=send_email_async)
            email_thread.daemon = True
            email_thread.start()
            
            messages.success(self.request, f'Welcome to Toad, {user.get_short_name()}! Please check your email to verify your account before you can start using Toad.')
        except Exception as e:
            logger.error(f"Failed to start email sending: {e}")
            messages.warning(self.request, f'Welcome to Toad, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
        
        # Redirect to login page immediately
        return redirect('accounts:login')
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect('pages:project_list')
        return super().dispatch(request, *args, **kwargs)

@login_required
def logout_view(request):
    """
    Custom logout view that handles both GET and POST requests
    """
    user_name = request.user.get_short_name()
    logout(request)
    messages.success(request, f'You have been logged out successfully. See you later, {user_name}!')
    return redirect('pages:home')

@login_required
def account_settings_view(request):
    """
    Main account settings view with profile update form only
    """
    profile_form = ProfileUpdateForm(instance=request.user)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                with transaction.atomic():
                    profile_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('accounts:account_settings')
            else:
                messages.error(request, 'Please correct the errors in the profile form.')
    
    context = {
        'profile_form': profile_form,
        'user': request.user,
    }
    return render(request, 'accounts/pages/account_settings.html', context)

@login_required
def change_password_view(request):
    """
    Dedicated password change view with enhanced security
    """
    form = CustomPasswordChangeForm(request.user)
    
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # Keep user logged in after password change
                update_session_auth_hash(request, user)
                
                # Log the password change for security
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f'Password changed for user: {user.email}')
            
            messages.success(
                request, 
                'Your password has been changed successfully! You remain logged in on this device.'
            )
            return redirect('accounts:account_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/pages/password_change.html', context)

@login_required
def delete_account_view(request):
    """
    Account deletion view with confirmation
    """
    form = AccountDeletionForm(request.user)
    
    if request.method == 'POST':
        form = AccountDeletionForm(request.user, request.POST)
        if form.is_valid():
            user_name = request.user.get_short_name()
            user_email = request.user.email
            
            # Log the account deletion
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Account deleted: {user_email} ({user_name})')
            
            # Delete the user account
            request.user.delete()
            
            messages.success(
                request, 
                f'Your account has been permanently deleted, {user_name}. We\'re sorry to see you go!'
            )
            return redirect('pages:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/pages/delete_account.html', context)

@login_required
def account_overview_view(request):
    """
    Account overview with statistics and recent activity
    """
    from pages.models import Project, Task
    
    # Get user statistics
    total_projects = Project.objects.filter(user=request.user).count()
    total_tasks = Task.objects.filter(project__user=request.user).count()
    completed_tasks = Task.objects.filter(project__user=request.user, completed=True).count()
    
    # Calculate completion rate
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100, 1)
    
    # Get recent projects
    recent_projects = Project.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'recent_projects': recent_projects,
    }
    return render(request, 'accounts/pages/account_overview.html', context)


def forgot_password_view(request):
    """
    Forgot password view
    """
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Send password reset email
                if send_password_reset_email(user, request):
                    messages.success(request, f'Password reset email sent to {email}. Please check your inbox and follow the instructions.')
                else:
                    messages.error(request, 'Failed to send password reset email. Please try again later.')
                
                return redirect('accounts:login')
            except User.DoesNotExist:
                # Don't reveal if user exists or not for security
                messages.success(request, f'If an account with {email} exists, a password reset email has been sent.')
                return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/pages/forgot_password.html', context)


def reset_password_view(request, token):
    """
    Password reset view
    """
    # Find user with this token
    try:
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('accounts:login')
    
    # Verify the token
    if not user.verify_password_reset_token(token):
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if not password1 or not password2:
            messages.error(request, 'Please fill in both password fields.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            # Set new password
            user.set_password(password1)
            user.clear_password_reset_token()
            user.save()
            
            messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
            return redirect('accounts:login')
    
    context = {
        'token': token,
    }
    return render(request, 'accounts/pages/reset_password.html', context)


def verify_email_view(request, token):
    """
    Verify user's email address using the provided token.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Find user with this token
    try:
        user = User.objects.get(email_verification_token=token)
        logger.info(f"Found user for verification token: {user.email}")
    except User.DoesNotExist:
        logger.warning(f"Invalid verification token attempted: {token}")
        messages.error(request, 'Invalid or expired verification link. Please request a new verification email.')
        return redirect('pages:home')
    
    # Verify the token
    if user.verify_email_token(token):
        logger.info(f"Email verification successful for user: {user.email}")
        messages.success(request, f'Email verified successfully! Welcome to Toad, {user.get_short_name()}!')
        
        # Log the user in if they're not already
        if not request.user.is_authenticated:
            login(request, user)
            logger.info(f"User logged in after email verification: {user.email}")
        
        # Ensure user is logged in (double-check for mobile)
        if not request.user.is_authenticated:
            login(request, user)
            logger.info(f"Re-logged in user after email verification: {user.email}")
        
        # Redirect to their first grid or project list
        from pages.models import Project
        try:
            grid_name = f"{user.first_name}'s First Grid"
            first_grid = Project.objects.filter(user=user, name=grid_name).first()
            if first_grid:
                logger.info(f"Redirecting to first grid: {first_grid.pk}")
                return redirect('pages:project_grid', pk=first_grid.pk)
            else:
                logger.info(f"Redirecting to project list for user: {user.email}")
                return redirect('pages:project_list')
        except Exception as e:
            logger.error(f"Error during redirect after email verification: {e}")
            return redirect('pages:project_list')
        
        # Fallback redirect in case the above doesn't work
        logger.info(f"Fallback redirect to project list for user: {user.email}")
        return redirect('pages:project_list')
    else:
        logger.warning(f"Email verification failed for user: {user.email}")
        messages.error(request, 'Invalid or expired verification link. Please request a new verification email.')
        return redirect('pages:home')


def resend_verification_email_view(request):
    """
    Resend verification email to the user.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                
                # Check if email is already verified
                if user.email_verified:
                    messages.info(request, 'Your email is already verified.')
                    return redirect('accounts:login')
                
                # Send verification email
                if send_verification_email(user, request):
                    messages.success(request, f'Verification email sent to {email}! Please check your inbox.')
                else:
                    messages.error(request, 'Failed to send verification email. Please try again later or contact support.')
                
                return redirect('accounts:login')
            except User.DoesNotExist:
                # Don't reveal if user exists or not for security
                messages.success(request, f'If an account with {email} exists, a verification email has been sent.')
                return redirect('accounts:login')
    
    # Show resend verification form
    return render(request, 'accounts/pages/resend_verification.html')
