from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from .forms import (
    EmailAuthenticationForm, 
    CustomUserCreationForm, 
    ProfileUpdateForm, 
    CustomPasswordChangeForm, 
    AccountDeletionForm
)

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
        login(self.request, form.get_user())
        messages.success(self.request, f'Welcome back, {form.get_user().get_short_name()}!')
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
    success_url = reverse_lazy('pages:project_list')
    
    def form_valid(self, form):
        """Create the user and log them in automatically"""
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Welcome to Toad, {user.get_short_name()}! Your account has been created.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect(self.success_url)
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
