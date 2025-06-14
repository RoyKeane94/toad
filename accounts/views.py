from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
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
