from django.urls import path
from .views import (
    LoginView, 
    RegisterFreeView, 
    RegisterPersonalView,
    RegisterChoicesView,
    RegisterTrialView,
    SecretRegistrationView,
    logout_view, 
    account_settings_view, 
    change_password_view, 
    delete_account_view,
    account_overview_view,
    verify_email_view,
    resend_verification_email_view,
    forgot_password_view,
    reset_password_view,
    preview_email_templates,
    beta_update_email_preview
)
from .stripe_django_views import (
    stripe_checkout_view,
    create_checkout_session,
    stripe_success_view,
    stripe_cancel_view,
    create_portal_session,
    stripe_webhook
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterChoicesView.as_view(), name='register_choices'),
    path('register/free/', RegisterFreeView.as_view(), name='register_free'),
    path('register/personal/', RegisterPersonalView.as_view(), name='register_personal'),
    path('register/trial/', RegisterTrialView.as_view(), name='register_trial'),
    path('register/barnabytoad/', SecretRegistrationView.as_view(), name='secret_registration'),
    path('logout/', logout_view, name='logout'),
    
    # Account Management
    path('overview/', account_overview_view, name='account_overview'),
    path('settings/', account_settings_view, name='account_settings'),
    path('settings/password/', change_password_view, name='change_password'),
    path('settings/delete/', delete_account_view, name='delete_account'),
    
    # Email Verification
    path('verify-email/<str:token>/', verify_email_view, name='verify_email'),
    path('resend-verification/', resend_verification_email_view, name='resend_verification'),
    
    # Password Reset
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', reset_password_view, name='reset_password'),

    # Email preview (development only)
    path('preview-emails/', preview_email_templates, name='preview_emails'),
    path('preview-beta-update/', beta_update_email_preview, name='beta_update_preview'),
    
    # Stripe integration
    path('stripe/checkout/', stripe_checkout_view, name='stripe_checkout'),
    path('stripe/create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('stripe/success/', stripe_success_view, name='stripe_success'),
    path('stripe/cancel/', stripe_cancel_view, name='stripe_cancel'),
    path('stripe/create-portal-session/', create_portal_session, name='create_portal_session'),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
]
