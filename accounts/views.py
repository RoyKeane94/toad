from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
from .forms import EmailAuthenticationForm

# Create your views here.

class LoginView(FormView):
    """
    Custom login view using email authentication
    """
    template_name = 'accounts/login.html'
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy('dashboard')  # Change this to your desired redirect URL
    
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

# Function-based view alternative (if you prefer)
def login_view(request):
    """
    Function-based login view
    """
    if request.user.is_authenticated:
        return redirect('dashboard')  # Change to your desired redirect URL
    
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f'Welcome back, {form.get_user().get_short_name()}!')
            return redirect('dashboard')  # Change to your desired redirect URL
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})
