from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import LoginView, login_view, RegisterView, register_view

app_name = 'accounts'

urlpatterns = [
    # Class-based views (recommended)
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    
    # Function-based view alternatives (uncomment if you prefer this approach)
    # path('login/', login_view, name='login'),
    # path('register/', register_view, name='register'),
    
    # Logout view
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
]
