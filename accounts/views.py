from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import EmailAuthenticationForm, CustomUserCreationForm

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
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:account_settings')
    
    return render(request, 'accounts/account_settings.html')

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:account_settings')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/account_settings.html', {'password_form': form})

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/delete_account.html')
