from django.urls import path
from django.shortcuts import redirect
from .views import (
    LoginView, 
    RegisterFreeView, 
    RegisterPersonalView,
    RegisterProView,
    RegisterChoicesView,
    RegisterTrialView,
    Register3MonthTrialView,
    Register1MonthProTrialView,
    Register3MonthProTrialView,
    Register6MonthProTrialView,
    RegisterTeamQuantityView,
    RegisterTeamAdminView,
    RegisterTeamTrialQuantityView,
    RegisterTeamTrialAdminView,
    logout_view, 
    account_settings_view, 
    change_password_view, 
    delete_account_view,
    account_overview_view,
    verify_email_view,
    resend_verification_email_view,
    forgot_password_view,
    reset_password_view,
    unsubscribe_view,
    preview_email_templates,
    beta_update_email_preview,
    beta_feedback_email_preview,
    student_follow_up_email_preview,
    two_day_follow_up_email_preview,
    manage_subscription_view,
    downgrade_to_free_view,
    downgrade_to_personal_view,
    team_invite_members_view,
    manage_team_view,
    remove_team_member_view,
    cancel_team_subscription_view,
    increase_team_seats_view,
    reduce_team_seats_view,
    transfer_team_admin_view,
    cancel_team_invitation_view,
    accept_team_invitation_view,
    trial_not_eligible_view,
    start_team_trial_view
)
from .passwordless_views import RequestLoginCodeView, VerifyLoginCodeView

def secret_registration_redirect(request):
    """Redirect secret registration to 3-month pro trial registration"""
    return redirect('accounts:register_3_month_pro_trial')
from .stripe_django_views import (
    stripe_checkout_view,
    create_checkout_session,
    stripe_success_view,
    stripe_cancel_view,
    stripe_checkout_pro_view,
    stripe_checkout_pro_direct_view,
    create_checkout_session_pro,
    stripe_success_pro_view,
    stripe_cancel_pro_view,
    stripe_checkout_team_view,
    create_checkout_session_team,
    stripe_success_team_view,
    stripe_cancel_team_view,
    stripe_checkout_team_registration_view,
    create_portal_session,
    stripe_webhook,
    stripe_checkout_seat_change_view,
    stripe_success_seat_change_view,
    validate_promo_code
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('login/passwordless/', RequestLoginCodeView.as_view(), name='passwordless_request'),
    path('login/passwordless/verify/', VerifyLoginCodeView.as_view(), name='passwordless_verify'),
    path('register/', RegisterChoicesView.as_view(), name='register_choices'),
    path('register/pro/', RegisterProView.as_view(), name='register_pro'),
    path('register/team/quantity/', RegisterTeamQuantityView.as_view(), name='register_team_quantity'),
    path('register/team/admin/', RegisterTeamAdminView.as_view(), name='register_team_admin'),
    path('register/trial/', RegisterTrialView.as_view(), name='register_trial'),
    path('register/trial-3-month/', Register3MonthTrialView.as_view(), name='register_3_month_trial'),
    path('register/trial-1-month-pro/', Register1MonthProTrialView.as_view(), name='register_1_month_pro_trial'),
    path('register/trial-not-eligible/', trial_not_eligible_view, name='trial_not_eligible'),
    path('start-team-trial/', start_team_trial_view, name='start_team_trial'),
    path('register/trial-3-month-pro/', Register3MonthProTrialView.as_view(), name='register_3_month_pro_trial'),
    path('register/trial-6-month-pro/', Register6MonthProTrialView.as_view(), name='register_6_month_pro_trial'),
    path('register/team-trial/quantity/', RegisterTeamTrialQuantityView.as_view(), name='register_team_trial_quantity'),
    path('register/team-trial/admin/', RegisterTeamTrialAdminView.as_view(), name='register_team_trial_admin'),
    path('register/barnabytoad/', secret_registration_redirect, name='secret_registration'),
    path('logout/', logout_view, name='logout'),
    
    # Account Management
    path('overview/', account_overview_view, name='account_overview'),
    path('settings/', account_settings_view, name='account_settings'),
    path('settings/password/', change_password_view, name='change_password'),
    path('settings/delete/', delete_account_view, name='delete_account'),
    path('manage-subscription/', manage_subscription_view, name='manage_subscription'),
    path('downgrade-to-free/', downgrade_to_free_view, name='downgrade_to_free'),
    path('downgrade-to-personal/', downgrade_to_personal_view, name='downgrade_to_personal'),
    
    # Email Verification
    path('verify-email/<str:token>/', verify_email_view, name='verify_email'),
    path('resend-verification/', resend_verification_email_view, name='resend_verification'),
    
    # Password Reset
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', reset_password_view, name='reset_password'),
    
    # Email Management
    path('unsubscribe/<int:user_id>/', unsubscribe_view, name='unsubscribe'),

    # Email preview (development only)
    path('preview-emails/', preview_email_templates, name='preview_emails'),
    path('preview-beta-update/', beta_update_email_preview, name='beta_update_preview'),
    path('preview-beta-feedback/', beta_feedback_email_preview, name='beta_feedback_preview'),
    path('preview-student-follow-up/', student_follow_up_email_preview, name='student_follow_up_preview'),
    path('preview-2-day-follow-up/', two_day_follow_up_email_preview, name='two_day_follow_up_preview'),
    
    # Stripe integration
    path('stripe/checkout/', stripe_checkout_view, name='stripe_checkout'),
    path('stripe/create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('stripe/success/', stripe_success_view, name='stripe_success'),
    path('stripe/cancel/', stripe_cancel_view, name='stripe_cancel'),
    path('stripe/checkout/pro/', stripe_checkout_pro_view, name='stripe_checkout_pro'),
    path('stripe/checkout/pro/direct/', stripe_checkout_pro_direct_view, name='stripe_checkout_pro_direct'),
    path('stripe/create-checkout-session/pro/', create_checkout_session_pro, name='create_checkout_session_pro'),
    path('stripe/success/pro/', stripe_success_pro_view, name='stripe_success_pro'),
    path('stripe/cancel/pro/', stripe_cancel_pro_view, name='stripe_cancel_pro'),
    path('stripe/checkout/team/', stripe_checkout_team_view, name='stripe_checkout_team'),
    path('stripe/checkout/team/registration/', stripe_checkout_team_registration_view, name='stripe_checkout_team_registration'),
    path('stripe/create-checkout-session/team/', create_checkout_session_team, name='create_checkout_session_team'),
    path('stripe/success/team/', stripe_success_team_view, name='stripe_success_team'),
    path('stripe/cancel/team/', stripe_cancel_team_view, name='stripe_cancel_team'),
    path('stripe/create-portal-session/', create_portal_session, name='create_portal_session'),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    path('stripe/checkout/seat-change/', stripe_checkout_seat_change_view, name='stripe_checkout_seat_change'),
    path('stripe/success/seat-change/', stripe_success_seat_change_view, name='stripe_success_seat_change'),
    path('stripe/validate-promo-code/', validate_promo_code, name='validate_promo_code'),
    
    # Team Management
    path('team/invite-members/', team_invite_members_view, name='team_invite_members'),
    path('team/manage/', manage_team_view, name='manage_team'),
    path('team/remove-member/<int:user_id>/', remove_team_member_view, name='remove_team_member'),
    path('team/cancel/', cancel_team_subscription_view, name='cancel_team_subscription'),
    path('team/increase-seats/', increase_team_seats_view, name='increase_team_seats'),
    path('team/reduce-seats/', reduce_team_seats_view, name='reduce_team_seats'),
    path('team/transfer-admin/<int:user_id>/', transfer_team_admin_view, name='transfer_team_admin'),
    path('team/cancel-invitation/<int:invitation_id>/', cancel_team_invitation_view, name='cancel_team_invitation'),
    path('team/accept-invitation/<str:token>/', accept_team_invitation_view, name='accept_team_invitation'),
]
