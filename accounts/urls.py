from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import LoginView, login_view

app_name = 'accounts'

urlpatterns = [
    # Class-based view (recommended)
    path('login/', LoginView.as_view(), name='login'),
    
    # Function-based view alternative (uncomment if you prefer this approach)
    # path('login/', login_view, name='login'),
    
    # Logout view
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
]
