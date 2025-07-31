from django.urls import path
from .views import (
    LoginView, 
    RegisterView, 
    logout_view, 
    account_settings_view, 
    change_password_view, 
    delete_account_view,
    account_overview_view,
    verify_email_view,
    resend_verification_email_view
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Account Management
    path('overview/', account_overview_view, name='account_overview'),
    path('settings/', account_settings_view, name='account_settings'),
    path('settings/password/', change_password_view, name='change_password'),
    path('settings/delete/', delete_account_view, name='delete_account'),
    
    # Email Verification
    path('verify-email/<str:token>/', verify_email_view, name='verify_email'),
    path('resend-verification/', resend_verification_email_view, name='resend_verification'),
]
