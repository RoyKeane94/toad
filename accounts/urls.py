from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import LoginView, RegisterView, account_settings_view, change_password_view, delete_account_view

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
    
    # Account Settings
    path('settings/', account_settings_view, name='account_settings'),
    path('settings/password/', change_password_view, name='change_password'),
    path('settings/delete/', delete_account_view, name='delete_account'),
]
