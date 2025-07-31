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
    AccountDeletionForm
)
from .email_utils import send_verification_email

# Create your views here.

class LoginView(FormView):
    """
    Custom login view using email authentication
    """
    template_name = 'accounts/login.html'
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy('pages:project_list')  # Updated to project list
    
    def form_valid(self, form):
        """Login the user and redirect to success URL"""
        user = form.get_user()
        
        # Check if email is verified
        if not user.email_verified:
            messages.error(self.request, 'Please verify your email address before logging in. Check your inbox for the verification link.')
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
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and send verification email"""
        user = form.save()
        
        # Send verification email
        if send_verification_email(user, self.request):
            messages.success(self.request, f'Welcome to Toad, {user.get_short_name()}! Please check your email to verify your account before you can start using Toad.')
        else:
            messages.warning(self.request, f'Welcome to Toad, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
        
        # Redirect to login page instead of auto-login
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
    return render(request, 'accounts/account_settings.html', context)

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
    return render(request, 'accounts/password_change.html', context)

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
    return render(request, 'accounts/delete_account.html', context)

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
    return render(request, 'accounts/account_overview.html', context)


def verify_email_view(request, token):
    """
    Verify user's email address using the provided token.
    """
    # Find user with this token
    try:
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link. Please request a new verification email.')
        return redirect('pages:home')
    
    # Verify the token
    if user.verify_email_token(token):
        messages.success(request, f'Email verified successfully! Welcome to Toad, {user.get_short_name()}!')
        
        # Log the user in if they're not already
        if not request.user.is_authenticated:
            login(request, user)
        
        # Redirect to their first grid or project list
        from pages.models import Project
        try:
            grid_name = f"{user.first_name}'s First Grid"
            first_grid = Project.objects.filter(user=user, name=grid_name).first()
            if first_grid:
                return redirect('pages:project_grid', pk=first_grid.pk)
            else:
                return redirect('pages:project_list')
        except Exception:
            return redirect('pages:project_list')
    else:
        messages.error(request, 'Invalid or expired verification link. Please request a new verification email.')
        return redirect('pages:home')


def resend_verification_email_view(request):
    """
    Resend verification email to the user.
    """
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to request a verification email.')
        return redirect('accounts:login')
    
    user = request.user
    
    # Check if email is already verified
    if user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('pages:project_list')
    
    # Send verification email
    if send_verification_email(user, request):
        messages.success(request, 'Verification email sent! Please check your inbox.')
    else:
        messages.error(request, 'Failed to send verification email. Please try again later or contact support.')
    
    return redirect('accounts:account_settings')
