from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.http import Http404
from .models import User
from .forms import (
    EmailAuthenticationForm, 
    CustomUserCreationForm, 
    ProfileUpdateForm, 
    CustomPasswordChangeForm, 
    AccountDeletionForm,
    ForgotPasswordForm,
    TeamInvitationAcceptanceForm
)
from .email_utils import send_verification_email, send_password_reset_email, send_joining_email, send_team_invitation_email
import base64
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class LoginView(FormView):
    """
    Custom login view using email authentication
    """
    template_name = 'accounts/pages/login/login.html'
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy('pages:project_list')  # Updated to project list
    
    def get_context_data(self, **kwargs):
        """Add context for verification messages"""
        context = super().get_context_data(**kwargs)
        
        # Check if user just registered and needs verification
        if self.request.session.get('show_verification_message'):
            context['show_verification_message'] = True
            # Remove the flag so it only shows once
            del self.request.session['show_verification_message']
        
        return context
    
    def form_valid(self, form):
        """Login the user and redirect to success URL"""
        user = form.get_user()
        
        # Check if email is verified (allow Personal plan users to proceed to checkout)
        if not user.email_verified and user.tier != 'personal':
            messages.error(
                self.request, 
                'Please verify your email address before logging in. Check your inbox and spam folder for the verification link. If you haven\'t received it, you can request a new verification email below.'
            )
            return redirect('accounts:login')
        
        login(self.request, user)
        messages.success(self.request, f'Welcome back, {user.get_short_name()}!')
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


@login_required
def manage_subscription_view(request):
    """
    Manage subscription page - shows current plan and upgrade/downgrade options
    """
    user = request.user
    
    # Get current tier display info
    tier_display = {
        'beta': 'Beta Access',
        'free': 'Free Plan', 
        'personal': 'Personal Plan',
        'personal_trial': 'Personal Trial Plan',
        'personal_3_month_trial': 'Personal 3 Month Trial Plan',
        'pro': 'Team Toad Plan',
        'pro_trial': 'Team Toad Trial Plan'
    }.get(user.tier, f"{user.tier.title()} Plan")
    
    # Get user's active grids for potential selection
    from pages.models import Project
    from django.core.serializers import serialize
    import json
    
    user_grids_queryset = Project.objects.filter(user=user, is_archived=False).order_by('created_at')
    
    # Serialize grids to JSON for JavaScript
    user_grids_json = []
    for grid in user_grids_queryset:
        user_grids_json.append({
            'id': grid.id,
            'name': grid.name,
            'created_at': grid.created_at.strftime('%b %d, %Y')
        })
    
    # Check if user is part of a team subscription
    team_admin = None
    if user.team_admin:
        team_admin = user.team_admin
    
    context = {
        'user': user,
        'tier_display': tier_display,
        'user_grids': json.dumps(user_grids_json),
        'team_admin': team_admin,
    }
    
    return render(request, 'accounts/pages/settings/manage_subscription.html', context)


@login_required
def downgrade_to_free_view(request):
    """
    Downgrade user to Free tier
    """
    if request.method != 'POST':
        return redirect('accounts:manage_subscription')
    
    user = request.user
    
    # Only allow downgrade if user is not already on free tier
    if user.tier == 'free':
        messages.info(request, 'You are already on the Free plan.')
        return redirect('accounts:manage_subscription')
    
    # Handle grid selection
    from pages.models import Project
    active_projects = Project.objects.filter(user=user, is_archived=False)
    
    if active_projects.count() > 2:
        # Get selected grids from form
        selected_grids_str = request.POST.get('selected_grids', '')
        if not selected_grids_str:
            messages.error(request, 'Please select which grids to keep active.')
            return redirect('accounts:manage_subscription')
        
        try:
            selected_grid_ids = [int(id.strip()) for id in selected_grids_str.split(',') if id.strip()]
            
            # Validate that exactly 2 grids are selected
            if len(selected_grid_ids) != 2:
                messages.error(request, 'Please select exactly 2 grids to keep active.')
                return redirect('accounts:manage_subscription')
            
            # Validate that all selected grids belong to the user
            selected_projects = Project.objects.filter(id__in=selected_grid_ids, user=user, is_archived=False)
            if selected_projects.count() != 2:
                messages.error(request, 'Invalid grid selection.')
                return redirect('accounts:manage_subscription')
            
            # Archive all other active grids
            projects_to_archive = active_projects.exclude(id__in=selected_grid_ids)
            archived_count = projects_to_archive.count()
            
            for project in projects_to_archive:
                project.is_archived = True
                project.save()
            
            messages.warning(request, f'Downgraded to Free plan. {archived_count} grids have been archived to comply with the 2-grid limit.')
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid grid selection format.')
            return redirect('accounts:manage_subscription')
    else:
        messages.success(request, 'Successfully downgraded to Free plan.')
    
    # Update user tier
    user.tier = 'free'
    user.save()
    
    return redirect('accounts:manage_subscription')

class RegisterFreeView(FormView):
    """
    Custom registration view using email authentication
    """
    template_name = 'accounts/pages/registration/register_free.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and send verification email"""
        user = form.save()
        
        # Set user tier to Free
        user.tier = 'free'
        user.save()
        
        # Log registration attempt
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"New Free plan user registration: {user.email} ({user.get_short_name()})")
        
        # Add session flag immediately for better UX
        self.request.session['show_verification_message'] = True
        
        # Send verification email asynchronously to improve performance
        try:
            import threading
            def send_email_async():
                try:
                    email_sent = send_verification_email(user, self.request)
                    logger.info(f"Verification email sent: {email_sent} for {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send verification email to {user.email}: {e}")
            
            # Start email sending in background thread
            email_thread = threading.Thread(target=send_email_async)
            email_thread.daemon = True
            email_thread.start()
            
            messages.success(self.request, f'Welcome to Toad, {user.get_short_name()}! Please check your email to verify your account before you can start using Toad.')
        except Exception as e:
            logger.error(f"Failed to start email sending: {e}")
            messages.warning(self.request, f'Welcome to Toad, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
        
        # Redirect to login page immediately
        return redirect('accounts:login')
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect('pages:project_list')
        return super().dispatch(request, *args, **kwargs)


@login_required
def manage_subscription_view(request):
    """
    Manage subscription page - shows current plan and upgrade/downgrade options
    """
    user = request.user
    
    # Get current tier display info
    tier_display = {
        'beta': 'Beta Access',
        'free': 'Free Plan', 
        'personal': 'Personal Plan',
        'personal_trial': 'Personal Trial Plan',
        'personal_3_month_trial': 'Personal 3 Month Trial Plan',
        'pro': 'Team Toad Plan',
        'pro_trial': 'Team Toad Trial Plan'
    }.get(user.tier, f"{user.tier.title()} Plan")
    
    # Get user's active grids for potential selection
    from pages.models import Project
    from django.core.serializers import serialize
    import json
    
    user_grids_queryset = Project.objects.filter(user=user, is_archived=False).order_by('created_at')
    
    # Serialize grids to JSON for JavaScript
    user_grids_json = []
    for grid in user_grids_queryset:
        user_grids_json.append({
            'id': grid.id,
            'name': grid.name,
            'created_at': grid.created_at.strftime('%b %d, %Y')
        })
    
    # Check if user is part of a team subscription
    team_admin = None
    if user.team_admin:
        team_admin = user.team_admin
    
    context = {
        'user': user,
        'tier_display': tier_display,
        'user_grids': json.dumps(user_grids_json),
        'team_admin': team_admin,
    }
    
    return render(request, 'accounts/pages/settings/manage_subscription.html', context)


@login_required
def downgrade_to_free_view(request):
    """
    Downgrade user to Free tier
    """
    if request.method != 'POST':
        return redirect('accounts:manage_subscription')
    
    user = request.user
    
    # Only allow downgrade if user is not already on free tier
    if user.tier == 'free':
        messages.info(request, 'You are already on the Free plan.')
        return redirect('accounts:manage_subscription')
    
    # Handle grid selection
    from pages.models import Project
    active_projects = Project.objects.filter(user=user, is_archived=False)
    
    if active_projects.count() > 2:
        # Get selected grids from form
        selected_grids_str = request.POST.get('selected_grids', '')
        if not selected_grids_str:
            messages.error(request, 'Please select which grids to keep active.')
            return redirect('accounts:manage_subscription')
        
        try:
            selected_grid_ids = [int(id.strip()) for id in selected_grids_str.split(',') if id.strip()]
            
            # Validate that exactly 2 grids are selected
            if len(selected_grid_ids) != 2:
                messages.error(request, 'Please select exactly 2 grids to keep active.')
                return redirect('accounts:manage_subscription')
            
            # Validate that all selected grids belong to the user
            selected_projects = Project.objects.filter(id__in=selected_grid_ids, user=user, is_archived=False)
            if selected_projects.count() != 2:
                messages.error(request, 'Invalid grid selection.')
                return redirect('accounts:manage_subscription')
            
            # Archive all other active grids
            projects_to_archive = active_projects.exclude(id__in=selected_grid_ids)
            archived_count = projects_to_archive.count()
            
            for project in projects_to_archive:
                project.is_archived = True
                project.save()
            
            messages.warning(request, f'Downgraded to Free plan. {archived_count} grids have been archived to comply with the 2-grid limit.')
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid grid selection format.')
            return redirect('accounts:manage_subscription')
    else:
        messages.success(request, 'Successfully downgraded to Free plan.')
    
    # Update user tier
    user.tier = 'free'
    user.save()
    
    return redirect('accounts:manage_subscription')

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
    
    # Check if user is a team admin
    from accounts.models import SubscriptionGroup, TeamInvitation
    subscription_group = None
    team_members = []
    pending_invitations = []
    current_members_count = 0
    pending_count = 0
    available_seats = 0
    total_seats = 0
    
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    if subscription_group:
        team_members = subscription_group.members.all()
        pending_invitations = TeamInvitation.objects.filter(
            subscription_group=subscription_group,
            status='pending'
        ).order_by('-created_at')[:5]  # Show last 5 pending invitations
        pending_count = TeamInvitation.objects.filter(
            subscription_group=subscription_group,
            status='pending'
        ).count()
        current_members_count = subscription_group.get_active_members_count()
        available_seats = subscription_group.quantity - current_members_count - pending_count
        total_seats = subscription_group.quantity
    
    context = {
        'profile_form': profile_form,
        'user': request.user,
        'subscription_group': subscription_group,
        'team_members': team_members,
        'pending_invitations': pending_invitations,
        'current_members_count': current_members_count,
        'pending_count': pending_count,
        'available_seats': available_seats,
        'total_seats': total_seats,
    }
    return render(request, 'accounts/pages/settings/account_settings.html', context)

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
    return render(request, 'accounts/pages/settings/password_change.html', context)

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
    return render(request, 'accounts/pages/settings/delete_account.html', context)

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
    return render(request, 'accounts/pages/settings/account_overview.html', context)


def forgot_password_view(request):
    """
    Forgot password view
    """
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Send password reset email
                if send_password_reset_email(user, request):
                    messages.success(request, f'Password reset email sent to {email}. Please check your inbox and follow the instructions.')
                else:
                    messages.error(request, 'Failed to send password reset email. Please try again later.')
                
                return redirect('accounts:login')
            except User.DoesNotExist:
                # Don't reveal if user exists or not for security
                messages.success(request, f'If an account with {email} exists, a password reset email has been sent.')
                return redirect('accounts:login')
    else:
        form = ForgotPasswordForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/pages/settings/forgot_password.html', context)


def reset_password_view(request, token):
    """
    Password reset view
    """
    # Find user with this token
    try:
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('accounts:login')
    
    # Verify the token
    if not user.verify_password_reset_token(token):
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if not password1 or not password2:
            messages.error(request, 'Please fill in both password fields.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            # Set new password
            user.set_password(password1)
            user.clear_password_reset_token()
            user.save()
            
            messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
            return redirect('accounts:login')
    
    context = {
        'token': token,
    }
    return render(request, 'accounts/pages/settings/reset_password.html', context)


def verify_email_view(request, token):
    """
    Verify user's email address using the provided token.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Find user with this token
    try:
        user = User.objects.get(email_verification_token=token)
        logger.info(f"Found user for verification token: {user.email}")
    except User.DoesNotExist:
        logger.warning(f"Invalid verification token attempted: {token}")
        messages.error(request, 'Invalid or expired verification link. Please request a new verification email.')
        return redirect('pages:home')
    
    # Verify the token
    if user.verify_email_token(token):
        logger.info(f"Email verification successful for user: {user.email}")
        
        # Always log the user in after successful verification
        # Force login regardless of current authentication state
        login(request, user)
        logger.info(f"User automatically logged in after email verification: {user.email}")
        
        messages.success(request, f'Email verified successfully! Welcome to Toad, {user.get_short_name()}! You are now signed in.')
        
        # Send joining email in background (best-effort)
        try:
            import threading
            from django.conf import settings
            from django.urls import reverse
            
            # Use reverse to get the correct URL path
            project_list_path = reverse('pages:project_list')
            base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
            cta_url = f"{base_url}{project_list_path}" if base_url else None
            threading.Thread(target=lambda: send_joining_email(user, request, cta_url)).start()
        except Exception as e:
            logger.error(f"Failed to queue joining email for {user.email}: {e}")

        # Redirect to their first grid or project list
        from pages.models import Project
        try:
            # Check if user has any projects
            user_projects = Project.objects.filter(user=user).order_by('created_at')
            
            if user_projects.exists():
                # User has projects, redirect to their first project
                first_project = user_projects.first()
                logger.info(f"Redirecting to first project: {first_project.pk}")
                return redirect('pages:project_grid', pk=first_project.pk)
            else:
                # User has no projects, redirect to project list to create their first one
                logger.info(f"Redirecting to project list for new user: {user.email}")
                return redirect('pages:project_list')
                
        except Exception as e:
            logger.error(f"Error during redirect after email verification: {e}")
            return redirect('pages:project_list')
    else:
        logger.warning(f"Email verification failed for user: {user.email}")
        messages.error(request, 'Invalid or expired verification link. Please request a new verification email.')
        return redirect('pages:home')


def resend_verification_email_view(request):
    """
    Resend verification email to the user.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                
                # Check if email is already verified
                if user.email_verified:
                    messages.warning(request, f'Your email ({email}) is already verified. You can sign in directly.')
                    return redirect('accounts:login')
                
                # Send verification email
                if send_verification_email(user, request):
                    messages.success(request, f'Verification email sent to {email}! Please check your inbox.')
                else:
                    messages.error(request, 'Failed to send verification email. Please try again later or contact support.')
                
                return redirect('accounts:login')
            except User.DoesNotExist:
                # Don't reveal if user exists or not for security
                messages.success(request, f'If an account with {email} exists, a verification email has been sent.')
                return redirect('accounts:login')
            except Exception as e:
                messages.error(request, 'An error occurred while processing your request. Please try again later.')
                return redirect('accounts:login')
    
    # Show resend verification form
    return render(request, 'accounts/pages/registration/resend_verification.html')


def unsubscribe_view(request, user_id):
    """
    Unsubscribe user from emails
    """
    try:
        user = User.objects.get(id=user_id)
        user.email_subscribed = False
        user.save(update_fields=['email_subscribed'])
        
        messages.success(request, f'You have been unsubscribed from Toad emails. We\'re sorry to see you go!')
        
        # Log the unsubscribe
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'User unsubscribed from emails: {user.email} (ID: {user_id})')
        
    except User.DoesNotExist:
        messages.error(request, 'Invalid unsubscribe link.')
    
    return redirect('pages:home')


def preview_email_templates(request):
    """Test view to preview email templates"""
    from django.template.loader import render_to_string
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Create a test user
    test_user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Test URLs
    verification_url = 'https://example.com/verify/abc123'
    reset_url = 'https://example.com/reset/xyz789'
    
    # Render email templates
    email_verification_html = render_to_string('accounts/email/email_verification.html', {
        'user': test_user,
        'verification_url': verification_url
    })
    
    password_reset_html = render_to_string('accounts/email/password_reset_email.html', {
        'user': test_user,
        'reset_url': reset_url
    })
    
    # Render student follow-up email
    student_follow_up_html = render_to_string('accounts/email/student/student_follow_up_prompt_email.html', {
        'user': test_user
    })
    
    return render(request, 'accounts/email_preview.html', {
        'email_verification_html': email_verification_html,
        'password_reset_html': password_reset_html,
        'student_follow_up_html': student_follow_up_html
    })

def beta_update_email_preview(request):
    """Preview the beta update email template"""
    # Load the Toad image if it exists
    toad_image_data = None
    try:
        image_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'Toad Email Image.png')
        if os.path.exists(image_path):
            with open(image_path, 'rb') as image_file:
                toad_image_data = base64.b64encode(image_file.read()).decode('utf-8')
    except (IndexError, FileNotFoundError):
        pass
    
    # Render the beta update email template
    from django.template.loader import render_to_string
    beta_update_html = render_to_string('accounts/email/beta_update_email.html', {
        'toad_image_data': toad_image_data
    })
    
    # Return the rendered HTML directly
    from django.http import HttpResponse
    return HttpResponse(beta_update_html)


def student_follow_up_email_preview(request):
    """Preview the student follow-up email template"""
    from django.template.loader import render_to_string
    from django.contrib.auth import get_user_model
    from django.http import HttpResponse
    
    User = get_user_model()
    
    # Create a test user
    test_user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Render the student follow-up email template
    student_follow_up_html = render_to_string('accounts/email/student/student_follow_up_prompt_email.html', {
        'user': test_user
    })
    
    # Return the rendered HTML directly
    return HttpResponse(student_follow_up_html)


def two_day_follow_up_email_preview(request):
    """Preview the 2-day follow-up email template"""
    from django.template.loader import render_to_string
    from django.contrib.auth import get_user_model
    from django.http import HttpResponse
    
    User = get_user_model()
    
    # Use the logged-in user if available, otherwise use a test user
    if request.user.is_authenticated:
        test_user = request.user
    else:
        # Create or get a test user
        test_user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'tier': 'free'  # Test with a free user to see Pro promotion
            }
        )
    
    # Get base URL
    base_url = getattr(settings, 'BASE_URL', 'https://www.meettoad.co.uk')
    
    # Render the 2-day follow-up email template
    email_html = render_to_string('accounts/email/follow_up/2_day_follow_up_email.html', {
        'user': test_user,
        'base_url': base_url
    })
    
    # Return the rendered HTML directly
    return HttpResponse(email_html)


class RegisterChoicesView(TemplateView):
    """
    View to display pricing plan choices
    """
    template_name = 'accounts/pages/registration/register_choices.html'


class RegisterPersonalView(FormView):
    """
    Custom registration view for Personal plan using email authentication
    """
    template_name = 'accounts/pages/registration/register_personal.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and redirect to Stripe checkout"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Starting Personal plan user registration...")
            user = form.save()
            logger.info(f"User created successfully: {user.email}")
            
            # Set user tier to FREE initially - will be upgraded to personal after successful payment
            if hasattr(user, 'tier'):
                user.tier = 'free'  # Default to free tier
                user.save()
                logger.info(f"User tier set to free: {user.email}")
            
            # Log registration attempt
            logger.info(f"New Personal plan user registration: {user.email} ({user.get_short_name()}) - tier set to FREE initially")
            
            # Log the user in immediately so they can proceed to checkout
            logger.info("Logging user in...")
            login(self.request, user)
            logger.info("User logged in successfully")
            
            # Redirect to Stripe checkout for Personal plan
            logger.info("Redirecting to Stripe checkout...")
            messages.success(self.request, 'Account created successfully! Please complete your subscription to activate Personal features.')
            return redirect('accounts:stripe_checkout')
            
        except Exception as e:
            logger.error(f"Error in RegisterPersonalView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class RegisterProView(FormView):
    """
    Custom registration view for Pro plan using email authentication
    """
    template_name = 'accounts/pages/registration/register_pro.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and redirect to Stripe checkout"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Starting Pro plan user registration...")
            user = form.save()
            logger.info(f"User created successfully: {user.email}")
            
            # Set user tier to FREE initially - will be upgraded to pro after successful payment
            if hasattr(user, 'tier'):
                user.tier = 'free'  # Default to free tier
                user.save()
                logger.info(f"User tier set to free: {user.email}")
            
            # Log registration attempt
            logger.info(f"New Pro plan user registration: {user.email} ({user.get_short_name()}) - tier set to FREE initially")
            
            # Log the user in immediately so they can proceed to checkout
            logger.info("Logging user in...")
            login(self.request, user)
            logger.info("User logged in successfully")
            
            # Redirect to Stripe checkout for Pro plan
            logger.info("Redirecting to Stripe checkout...")
            messages.success(self.request, 'Account created successfully! Please complete your subscription to activate Pro features.')
            return redirect('accounts:stripe_checkout_pro')
            
        except Exception as e:
            logger.error(f"Error in RegisterProView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class RegisterTeamQuantityView(TemplateView):
    """
    Step 1: View for choosing number of team members
    """
    template_name = 'accounts/pages/registration/register_team_quantity.html'
    
    def post(self, request, *args, **kwargs):
        """Handle quantity selection"""
        try:
            quantity = int(request.POST.get('quantity', 2))
            if quantity < 2:
                messages.error(request, 'Team subscription requires at least 2 seats.')
                return self.get(request, *args, **kwargs)
            if quantity > 100:
                messages.error(request, 'Maximum 100 seats allowed.')
                return self.get(request, *args, **kwargs)
            
            # Store quantity in session for next step
            request.session['team_registration_quantity'] = quantity
            request.session['team_registration_flow'] = True
            
            # Redirect to admin registration
            return redirect('accounts:register_team_admin')
        except ValueError:
            messages.error(request, 'Please enter a valid number.')
            return self.get(request, *args, **kwargs)


class RegisterTeamAdminView(FormView):
    """
    Step 2: Custom registration view for Team Toad admin (multiple users)
    """
    template_name = 'accounts/pages/registration/register_team_admin.html'
    form_class = CustomUserCreationForm
    
    def dispatch(self, request, *args, **kwargs):
        """Check if quantity is set in session"""
        if not request.session.get('team_registration_quantity'):
            messages.error(request, 'Please select team size first.')
            return redirect('accounts:register_team_quantity')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add quantity to context"""
        context = super().get_context_data(**kwargs)
        context['quantity'] = self.request.session.get('team_registration_quantity', 2)
        context['total_price'] = context['quantity'] * 5  # £5 per seat
        context['invite_count'] = context['quantity'] - 1
        return context
    
    def form_valid(self, form):
        """Create the admin user and redirect to Stripe checkout"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            quantity = self.request.session.get('team_registration_quantity', 2)
            
            logger.info(f"Starting Team Toad admin registration with {quantity} seats...")
            user = form.save()
            logger.info(f"Admin user created successfully: {user.email}")
            
            # Set user tier to FREE initially - will be upgraded to pro after successful payment
            if hasattr(user, 'tier'):
                user.tier = 'free'  # Default to free tier
                user.save()
                logger.info(f"User tier set to free: {user.email}")
            
            # Log registration attempt
            logger.info(f"New Team Toad admin registration: {user.email} ({user.get_short_name()}) - tier set to FREE initially, {quantity} seats")
            
            # Log the user in immediately so they can proceed to checkout
            logger.info("Logging user in...")
            login(self.request, user)
            logger.info("User logged in successfully")
            
            # Keep quantity in session for checkout
            self.request.session['team_registration_quantity'] = quantity
            self.request.session['team_registration_flow'] = True
            
            # Redirect to Stripe checkout for Team plan
            logger.info("Redirecting to Stripe checkout...")
            messages.success(self.request, f'Account created successfully! Proceeding to payment for {quantity} seats.')
            return redirect('accounts:stripe_checkout_team_registration')
            
        except Exception as e:
            logger.error(f"Error in RegisterTeamAdminView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class RegisterTrialView(FormView):
    """
    Registration view for 6-month free trial users
    """
    template_name = 'accounts/pages/registration/register_trial.html'
    form_class = CustomUserCreationForm
    
    def get_context_data(self, **kwargs):
        """Add society and university info to context"""
        context = super().get_context_data(**kwargs)
        
        # Get society and university from URL parameters
        society_name = self.request.GET.get('society', '')
        university_name = self.request.GET.get('university', '')
        
        context['society_name'] = society_name
        context['university_name'] = university_name
        
        return context
    
    def form_valid(self, form):
        """Create the user and start their trial - mirrors RegisterFreeView but with personal tier"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Get society and university info from URL parameters
            society_name = self.request.GET.get('society', '')
            university_name = self.request.GET.get('university', '')
            
            logger.info(f"Starting trial user registration... Society: {society_name}, University: {university_name}")
            user = form.save()
            logger.info(f"User created successfully: {user.email}")
            
            # Try to find and associate the society and university
            society_link = None
            university = None
            
            if society_name:
                try:
                    from CRM.models import SocietyLink, SocietyUniversity
                    from django.utils.text import slugify
                    
                    # Find society link by name
                    society_links = SocietyLink.objects.filter(
                        society_university__isnull=False
                    ).select_related('society_university')
                    
                    for link in society_links:
                        if slugify(link.name) == slugify(society_name):
                            society_link = link
                            university = link.society_university
                            break
                    
                    if society_link:
                        # Associate user with society and university
                        user.associated_society = society_link
                        user.associated_university = university
                        user.save()
                        
                        logger.info(f"User {user.email} associated with society: {society_link.name} and university: {university.name}")
                    else:
                        logger.warning(f"Could not find society link for: {society_name}")
                        
                except Exception as e:
                    logger.error(f"Error associating user with society/university: {e}")
            
            # Set user tier to personal for trial
            user.tier = 'personal'
            user.save()
            logger.info(f"User tier set to personal for trial: {user.email}")
            
            # Start 6-month trial
            user.start_trial(days=180)  # 6 months
            logger.info(f"Trial started for user: {user.email}, ends at: {user.trial_ends_at}")
            
            # Log registration attempt with society/university info
            if society_link and university:
                logger.info(f"New Trial plan user registration: {user.email} ({user.get_short_name()}) - tier set to PERSONAL for trial - Society: {society_link.name}, University: {university.name}")
            else:
                logger.info(f"New Trial plan user registration: {user.email} ({user.get_short_name()}) - tier set to PERSONAL for trial - No society/university association")
            
            # Add session flag immediately for better UX
            self.request.session['show_verification_message'] = True
            
            # Send verification email asynchronously to improve performance
            try:
                from .email_utils import send_verification_email
                import threading
                
                def send_email_async():
                    try:
                        email_sent = send_verification_email(user, self.request)
                        logger.info(f"Verification email sent: {email_sent} for {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to send verification email to {user.email}: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_email_async)
                email_thread.daemon = True
                email_thread.start()
                
                messages.success(self.request, f'Welcome to your 6-month free trial, {user.get_short_name()}! Please check your email to verify your account before you can start using Toad Personal features.')
            except Exception as e:
                logger.error(f"Failed to start email sending: {e}")
                messages.warning(self.request, f'Welcome to your 6-month free trial, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
            
            # Redirect to login page immediately (like RegisterFreeView)
            return redirect('accounts:login')
            
        except Exception as e:
            logger.error(f"Error in RegisterTrialView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class Register3MonthTrialView(FormView):
    """
    Registration view for 3-month free trial users
    """
    template_name = 'accounts/pages/registration/register_3_month_trial.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and start their 3-month trial"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            logger.info("Starting 3-month trial user registration...")
            user = form.save()
            logger.info(f"User created successfully: {user.email}")
            
            # Set user tier to personal_3_month_trial and start 3-month trial
            user.tier = 'personal_3_month_trial'
            user.trial_started_at = timezone.now()
            user.trial_ends_at = timezone.now() + timedelta(days=90)  # 3 months
            user.save()
            logger.info(f"User tier set to personal_3_month_trial: {user.email}")
            logger.info(f"3-month trial started for user: {user.email}, ends at: {user.trial_ends_at}")
            
            # Log registration attempt
            logger.info(f"New 3-Month Trial plan user registration: {user.email} ({user.get_short_name()}) - tier set to PERSONAL_3_MONTH_TRIAL")
            
            # Add session flag immediately for better UX
            self.request.session['show_verification_message'] = True
            
            # Send verification email asynchronously to improve performance
            try:
                from .email_utils import send_verification_email
                import threading
                
                def send_email_async():
                    try:
                        email_sent = send_verification_email(user, self.request)
                        logger.info(f"Verification email sent: {email_sent} for {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to send verification email to {user.email}: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_email_async)
                email_thread.daemon = True
                email_thread.start()
                
                messages.success(self.request, f'Welcome to your 3-month free trial, {user.get_short_name()}! Please check your email to verify your account before you can start using Toad Personal features.')
            except Exception as e:
                logger.error(f"Failed to start email sending: {e}")
                messages.warning(self.request, f'Welcome to your 3-month free trial, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
            
            # Redirect to login page immediately
            return redirect('accounts:login')
            
        except Exception as e:
            logger.error(f"Error in Register3MonthTrialView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect('pages:project_list')
        return super().dispatch(request, *args, **kwargs)


class Register1MonthProTrialView(FormView):
    """
    Registration view for 1-month Pro trial users
    """
    template_name = 'accounts/pages/registration/register_1_month_pro_trial.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and start their 1-month Pro trial"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            logger.info("Starting 1-month Pro trial user registration...")
            user = form.save()
            logger.info(f"User created successfully: {user.email}")
            
            # Set user tier to pro_trial and trial_type to 1_month
            # The signal will handle setting the correct trial duration
            user.tier = 'pro_trial'
            user.trial_type = '1_month'
            user.save()
            logger.info(f"User tier set to pro_trial with 1-month trial type: {user.email}")
            
            # Log registration attempt
            logger.info(f"New 1-Month Pro Trial plan user registration: {user.email} ({user.get_short_name()}) - tier set to PRO_TRIAL")
            
            # Add session flag immediately for better UX
            self.request.session['show_verification_message'] = True
            
            # Send verification email asynchronously to improve performance
            try:
                from .email_utils import send_verification_email
                import threading
                
                def send_email_async():
                    try:
                        email_sent = send_verification_email(user, self.request)
                        logger.info(f"Verification email sent: {email_sent} for {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to send verification email to {user.email}: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_email_async)
                email_thread.daemon = True
                email_thread.start()
                
                messages.success(self.request, f'Welcome to your 1-month Pro trial, {user.get_short_name()}! Please check your email to verify your account before you can start using Team Toad features.')
            except Exception as e:
                logger.error(f"Failed to start email sending: {e}")
                messages.warning(self.request, f'Welcome to your 1-month Pro trial, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
            
            # Redirect to login page immediately
            return redirect('accounts:login')
            
        except Exception as e:
            logger.error(f"Error in Register1MonthProTrialView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect('pages:project_list')
        return super().dispatch(request, *args, **kwargs)


class Register3MonthProTrialView(FormView):
    """
    Registration view for 3-month Pro trial users
    """
    template_name = 'accounts/pages/registration/register_3_month_pro_trial.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and start their 3-month Pro trial"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            logger.info("Starting 3-month Pro trial user registration...")
            user = form.save()
            logger.info(f"User created successfully: {user.email}")
            
            # Set user tier to pro_trial and trial_type to 3_month
            # The signal will handle setting the correct trial duration
            user.tier = 'pro_trial'
            user.trial_type = '3_month'
            user.save()
            logger.info(f"User tier set to pro_trial with 3-month trial type: {user.email}")
            
            # Log registration attempt
            logger.info(f"New 3-Month Pro Trial plan user registration: {user.email} ({user.get_short_name()}) - tier set to PRO_TRIAL")
            
            # Add session flag immediately for better UX
            self.request.session['show_verification_message'] = True
            
            # Send verification email asynchronously to improve performance
            try:
                from .email_utils import send_verification_email
                import threading
                
                def send_email_async():
                    try:
                        email_sent = send_verification_email(user, self.request)
                        logger.info(f"Verification email sent: {email_sent} for {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to send verification email to {user.email}: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_email_async)
                email_thread.daemon = True
                email_thread.start()
                
                messages.success(self.request, f'Welcome to your 3-month Pro trial, {user.get_short_name()}! Please check your email to verify your account before you can start using Team Toad features.')
            except Exception as e:
                logger.error(f"Failed to start email sending: {e}")
                messages.warning(self.request, f'Welcome to your 3-month Pro trial, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
            
            # Redirect to login page immediately
            return redirect('accounts:login')
            
        except Exception as e:
            logger.error(f"Error in Register3MonthProTrialView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect('pages:project_list')
        return super().dispatch(request, *args, **kwargs)


class Register6MonthProTrialView(FormView):
    """
    Registration view for 6-month Pro trial users
    """
    template_name = 'accounts/pages/registration/register_6_month_pro_trial.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and start their 6-month Pro trial"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            logger.info("Starting 6-month Pro trial user registration...")
            user = form.save()
            logger.info(f"User created successfully: {user.email}")
            
            # Set user tier to pro_trial and trial_type to 6_month
            # The signal will handle setting the correct trial duration
            user.tier = 'pro_trial'
            user.trial_type = '6_month'
            user.save()
            logger.info(f"User tier set to pro_trial with 6-month trial type: {user.email}")
            
            # Log registration attempt
            logger.info(f"New 6-Month Pro Trial plan user registration: {user.email} ({user.get_short_name()}) - tier set to PRO_TRIAL with 6-month duration")
            
            # Add session flag immediately for better UX
            self.request.session['show_verification_message'] = True
            
            # Send verification email asynchronously to improve performance
            try:
                from .email_utils import send_verification_email
                import threading
                
                def send_email_async():
                    try:
                        email_sent = send_verification_email(user, self.request)
                        logger.info(f"Verification email sent: {email_sent} for {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to send verification email to {user.email}: {e}")
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_email_async)
                email_thread.daemon = True
                email_thread.start()
                
                messages.success(self.request, f'Welcome to your 6-month Pro trial, {user.get_short_name()}! Please check your email to verify your account before you can start using Team Toad features.')
            except Exception as e:
                logger.error(f"Failed to start email sending: {e}")
                messages.warning(self.request, f'Welcome to your 6-month Pro trial, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
            
            # Redirect to login page immediately
            return redirect('accounts:login')
            
        except Exception as e:
            logger.error(f"Error in Register6MonthProTrialView.form_valid: {e}", exc_info=True)
            raise
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect('pages:project_list')
        return super().dispatch(request, *args, **kwargs)


class SecretRegistrationView(FormView):
    """
    Secret registration view for Beta users
    """
    template_name = 'accounts/pages/registration/secret_registration.html'
    form_class = CustomUserCreationForm
    
    def form_valid(self, form):
        """Create the user and send verification email"""
        user = form.save()
        
        # Set user tier to Society Pro
        user.tier = 'society_pro'
        user.save()
        
        # Log registration attempt
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"New Society Pro user registration: {user.email} ({user.get_short_name()})")
        
        # Add session flag immediately for better UX
        self.request.session['show_verification_message'] = True
        
        # Send verification email asynchronously to improve performance
        try:
            import threading
            def send_email_async():
                try:
                    email_sent = send_verification_email(user, self.request)
                    logger.info(f"Verification email sent: {email_sent} for {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send verification email to {user.email}: {e}")
            
            # Start email sending in background thread
            email_thread = threading.Thread(target=send_email_async)
            email_thread.daemon = True
            email_thread.start()
            
            messages.success(self.request, f'Welcome to Toad Society Pro, {user.get_short_name()}! Please check your email to verify your account before you can start using Toad.')
        except Exception as e:
            logger.error(f"Failed to start email sending: {e}")
            messages.warning(self.request, f'Welcome to Toad Society Pro, {user.get_short_name()}! Your account was created, but we couldn\'t send the verification email. Please contact support.')
        
        # Redirect to login page immediately
        return redirect('accounts:login')
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users away from registration page"""
        if request.user.is_authenticated:
            return redirect('pages:project_list')
        return super().dispatch(request, *args, **kwargs)


@login_required
def manage_subscription_view(request):
    """
    Manage subscription page - shows current plan and upgrade/downgrade options
    """
    user = request.user
    
    # Get current tier display info
    tier_display = {
        'beta': 'Beta Access',
        'free': 'Free Plan', 
        'personal': 'Personal Plan',
        'personal_trial': 'Personal Trial Plan',
        'personal_3_month_trial': 'Personal 3 Month Trial Plan',
        'pro': 'Team Toad Plan',
        'pro_trial': 'Team Toad Trial Plan'
    }.get(user.tier, f"{user.tier.title()} Plan")
    
    # Get user's active grids for potential selection
    from pages.models import Project
    from django.core.serializers import serialize
    import json
    
    user_grids_queryset = Project.objects.filter(user=user, is_archived=False).order_by('created_at')
    
    # Serialize grids to JSON for JavaScript
    user_grids_json = []
    for grid in user_grids_queryset:
        user_grids_json.append({
            'id': grid.id,
            'name': grid.name,
            'created_at': grid.created_at.strftime('%b %d, %Y')
        })
    
    # Check if user is part of a team subscription
    team_admin = None
    if user.team_admin:
        team_admin = user.team_admin
    
    context = {
        'user': user,
        'tier_display': tier_display,
        'user_grids': json.dumps(user_grids_json),
        'team_admin': team_admin,
    }
    
    return render(request, 'accounts/pages/settings/manage_subscription.html', context)


@login_required
def downgrade_to_free_view(request):
    """
    Downgrade user to Free tier
    """
    if request.method != 'POST':
        return redirect('accounts:manage_subscription')
    
    user = request.user
    
    # Only allow downgrade if user is not already on free tier
    if user.tier == 'free':
        messages.info(request, 'You are already on the Free plan.')
        return redirect('accounts:manage_subscription')
    
    # Handle grid selection
    from pages.models import Project
    active_projects = Project.objects.filter(user=user, is_archived=False)
    
    if active_projects.count() > 2:
        # Get selected grids from form
        selected_grids_str = request.POST.get('selected_grids', '')
        if not selected_grids_str:
            messages.error(request, 'Please select which grids to keep active.')
            return redirect('accounts:manage_subscription')
        
        try:
            selected_grid_ids = [int(id.strip()) for id in selected_grids_str.split(',') if id.strip()]
            
            # Validate that exactly 2 grids are selected
            if len(selected_grid_ids) != 2:
                messages.error(request, 'Please select exactly 2 grids to keep active.')
                return redirect('accounts:manage_subscription')
            
            # Validate that all selected grids belong to the user
            selected_projects = Project.objects.filter(id__in=selected_grid_ids, user=user, is_archived=False)
            if selected_projects.count() != 2:
                messages.error(request, 'Invalid grid selection.')
                return redirect('accounts:manage_subscription')
            
            # Archive all other active grids
            projects_to_archive = active_projects.exclude(id__in=selected_grid_ids)
            archived_count = projects_to_archive.count()
            
            for project in projects_to_archive:
                project.is_archived = True
                project.save()
            
            messages.warning(request, f'Downgraded to Free plan. {archived_count} grids have been archived to comply with the 2-grid limit.')
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid grid selection format.')
            return redirect('accounts:manage_subscription')
    else:
        messages.success(request, 'Successfully downgraded to Free plan.')
    
    # Update user tier
    user.tier = 'free'
    user.save()
    
    return redirect('accounts:manage_subscription')


@login_required
def downgrade_to_personal_view(request):
    """
    Downgrade user to Personal tier
    """
    if request.method != 'POST':
        return redirect('accounts:manage_subscription')
    
    user = request.user
    
    # Define pro tiers
    pro_tiers = ['pro', 'pro_trial', 'society_pro', 'beta']
    
    # Only allow downgrade if user is on a pro tier
    if user.tier not in pro_tiers:
        messages.info(request, 'You can only downgrade to Personal from a Pro plan.')
        return redirect('accounts:manage_subscription')
    
    # Update user tier to personal
    user.tier = 'personal'
    user.save()
    
    messages.success(request, 'Successfully downgraded to Personal plan.')
    return redirect('accounts:manage_subscription')


@login_required
def team_invite_members_view(request):
    """
    Page for admin to input emails for team members after team subscription purchase
    """
    from accounts.models import SubscriptionGroup
    
    # Get subscription group from session or from user's admin groups
    subscription_group_id = request.session.get('subscription_group_id')
    if not subscription_group_id:
        # Try to get from user's admin groups
        subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
        if not subscription_group:
            messages.error(request, 'No active team subscription found.')
            return redirect('accounts:manage_subscription')
    else:
        try:
            subscription_group = SubscriptionGroup.objects.get(id=subscription_group_id, admin=request.user)
            # Clear session after use
            del request.session['subscription_group_id']
        except SubscriptionGroup.DoesNotExist:
            messages.error(request, 'Invalid subscription group.')
            return redirect('accounts:manage_subscription')
    
    # Calculate available seats accounting for pending invitations
    from accounts.models import TeamInvitation
    current_members_count = subscription_group.get_active_members_count()
    pending_count = TeamInvitation.objects.filter(
        subscription_group=subscription_group,
        status='pending'
    ).count()
    available_seats = subscription_group.quantity - current_members_count - pending_count
    
    # Check if user is already a Team Toad user (pro, pro_trial, beta)
    pro_tiers = ['pro', 'pro_trial', 'beta']
    is_team_toad_user = request.user.tier in pro_tiers
    
    # Determine initial email fields - only show fields for available seats
    # If they are Team Toad user: show all empty fields (up to available seats)
    # If they are not: show their email in first field, rest empty (up to available seats)
    initial_emails = []
    if is_team_toad_user:
        # Show empty fields for available seats only
        initial_emails = [''] * available_seats
    else:
        # Show their email in first field if there's at least one available seat
        if available_seats > 0:
            initial_emails = [request.user.email] + [''] * (available_seats - 1)
        else:
            initial_emails = []
    
    if request.method == 'POST':
        # Get emails from form - handle both textarea and individual input fields
        emails = []
        
        # Check for individual email fields first (from the form with multiple inputs)
        email_fields = [key for key in request.POST.keys() if key.startswith('email_')]
        if email_fields:
            for key in sorted(email_fields):
                email = request.POST.get(key, '').strip()
                if email:
                    emails.append(email)
        else:
            # Fallback to textarea format
            emails_text = request.POST.get('emails', '')
            emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        emails = [email for email in emails if email not in seen and not seen.add(email)]
        
        # Allow partial submission - admin can leave fields empty and add them later
        # Only validate if they've entered emails
        if emails:
            # Check if we have enough seats (accounting for pending invitations)
            current_members_count = subscription_group.get_active_members_count()
            from accounts.models import TeamInvitation
            pending_count = TeamInvitation.objects.filter(
                subscription_group=subscription_group,
                status='pending'
            ).count()
            available_seats = subscription_group.quantity - current_members_count - pending_count
            
            if len(emails) > available_seats:
                messages.error(request, f'You can only invite {available_seats} more member(s). You have {subscription_group.quantity} total seats, {current_members_count} in use, and {pending_count} pending invitation(s).')
                return redirect('accounts:team_invite_members')
        
        # Create invitations
        from accounts.models import TeamInvitation
        from django.utils import timezone
        from datetime import timedelta
        
        created_count = 0
        skipped_count = 0
        
        for email in emails[:available_seats]:  # Only invite up to available seats
            # Skip if it's the admin's email
            if email.lower() == request.user.email.lower():
                skipped_count += 1
                continue
            
            # Check if email is already a member
            if subscription_group.members.filter(email=email).exists():
                skipped_count += 1
                continue
            
            # Check if invitation already exists and is pending
            if TeamInvitation.objects.filter(
                subscription_group=subscription_group,
                invited_email=email,
                status='pending'
            ).exists():
                skipped_count += 1
                continue
            
            # Create invitation
            invitation = TeamInvitation.objects.create(
                subscription_group=subscription_group,
                invited_by=request.user,
                invited_email=email,
                expires_at=timezone.now() + timedelta(days=7)  # 7 days to accept
            )
            
            # Send invitation email
            try:
                send_team_invitation_email(invitation, request=request)
                created_count += 1
            except Exception as e:
                logger.error(f"Error sending team invitation email to {email}: {e}")
        
        if created_count > 0:
            messages.success(request, f'Successfully sent {created_count} invitation(s).')
        if skipped_count > 0:
            messages.info(request, f'{skipped_count} email(s) were skipped (already members, pending invitations, or your own email).')
        if created_count == 0 and skipped_count == 0 and emails:
            messages.error(request, 'No invitations were sent. Please check your email addresses.')
        elif not emails:
            messages.info(request, 'No emails entered. You can add team members later from the team management page.')
        
        # Update Stripe subscription metadata with new team info
        from accounts.stripe_django_views import update_subscription_metadata_with_team_info
        update_subscription_metadata_with_team_info(subscription_group)
        
        return redirect('accounts:manage_team')
    
    # Calculate available seats accounting for pending invitations
    from accounts.models import TeamInvitation
    current_members_count = subscription_group.get_active_members_count()
    pending_count = TeamInvitation.objects.filter(
        subscription_group=subscription_group,
        status='pending'
    ).count()
    available_seats = subscription_group.quantity - current_members_count - pending_count
    
    context = {
        'subscription_group': subscription_group,
        'available_seats': available_seats,
        'total_seats': subscription_group.quantity,
        'current_members_count': current_members_count,
        'pending_count': pending_count,
        'initial_emails': initial_emails,
        'is_team_toad_user': is_team_toad_user,
    }
    
    return render(request, 'accounts/pages/team/invite_members.html', context)


@login_required
def manage_team_view(request):
    """
    Admin page to manage team subscription: view members, invite, remove, cancel, transfer
    """
    from accounts.models import SubscriptionGroup, TeamInvitation
    from accounts.stripe_django_views import update_subscription_metadata_with_team_info
    import stripe
    import os
    
    # Get user's subscription group as admin
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    
    if not subscription_group:
        messages.error(request, 'You are not an admin of any active team subscription.')
        return redirect('accounts:manage_subscription')
    
    # Get active members
    members = subscription_group.members.all()
    
    # Get pending invitations with expiration status
    pending_invitations = TeamInvitation.objects.filter(
        subscription_group=subscription_group,
        status='pending'
    ).order_by('-created_at')
    
    # Add expiration status to each invitation for template
    pending_invitations_list = []
    for invitation in pending_invitations:
        pending_invitations_list.append({
            'invitation': invitation,
            'is_expired': invitation.is_expired(),
        })
    
    # Get current seat usage (accounting for pending invitations)
    current_members_count = subscription_group.get_active_members_count()
    pending_count = pending_invitations.count()
    available_seats = subscription_group.quantity - current_members_count - pending_count
    
    # Calculate max reduction (can't reduce below current usage)
    max_reduction = subscription_group.quantity - current_members_count - pending_count
    
    # Sync quantity from Stripe to ensure it's up to date
    if subscription_group.stripe_subscription_id:
        try:
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            subscription = stripe.Subscription.retrieve(subscription_group.stripe_subscription_id)
            
            # Get the quantity from Stripe
            if subscription.get('items', {}).get('data'):
                stripe_quantity = subscription['items']['data'][0].get('quantity')
                if stripe_quantity is not None and stripe_quantity != subscription_group.quantity:
                    logger.info(f'Syncing SubscriptionGroup quantity from {subscription_group.quantity} to {stripe_quantity} (from Stripe)')
                    subscription_group.quantity = stripe_quantity
                    subscription_group.save(update_fields=['quantity'])
        except Exception as e:
            logger.warning(f"Could not sync subscription quantity from Stripe: {e}")
    
    # Update Stripe subscription metadata with current team info
    if subscription_group.stripe_subscription_id:
        try:
            from accounts.stripe_django_views import update_subscription_metadata_with_team_info
            update_subscription_metadata_with_team_info(subscription_group)
        except Exception as e:
            logger.warning(f"Could not update subscription metadata: {e}")
    
    # Retrieve Stripe subscription details to show current billing amount
    stripe_subscription_info = None
    if subscription_group.stripe_subscription_id:
        try:
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            subscription = stripe.Subscription.retrieve(subscription_group.stripe_subscription_id)
            
            # Get the price and quantity from the subscription
            if subscription['items']['data']:
                item = subscription['items']['data'][0]
                price_id = item['price']['id']
                quantity = item['quantity']
                
                # Retrieve price details
                price = stripe.Price.retrieve(price_id)
                unit_amount = price['unit_amount']  # Amount in cents
                currency = price['currency'].upper()
                
                # Calculate total amount
                total_amount_cents = unit_amount * quantity
                total_amount = total_amount_cents / 100  # Convert to dollars/pounds
                
                # Format currency symbol
                currency_symbol = '£' if currency == 'GBP' else '$' if currency == 'USD' else currency
                
                stripe_subscription_info = {
                    'quantity': quantity,
                    'unit_amount': unit_amount / 100,  # Per seat amount
                    'total_amount': total_amount,
                    'currency': currency,
                    'currency_symbol': currency_symbol,
                    'status': subscription['status'],
                    'current_period_end': subscription.get('current_period_end'),
                    'cancel_at_period_end': subscription.get('cancel_at_period_end', False),
                }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe subscription details: {e}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving Stripe subscription: {e}", exc_info=True)
    
    context = {
        'subscription_group': subscription_group,
        'members': members,
        'pending_invitations': pending_invitations_list,
        'available_seats': available_seats,
        'current_members_count': current_members_count,
        'pending_count': pending_count,
        'total_seats': subscription_group.quantity,
        'max_reduction': max_reduction,
        'min_seats_required': current_members_count + pending_count,
        'stripe_subscription_info': stripe_subscription_info,
    }
    
    return render(request, 'accounts/pages/team/manage_team.html', context)


@login_required
def remove_team_member_view(request, user_id):
    """
    Remove a team member from the subscription group
    """
    from accounts.models import SubscriptionGroup
    from django.shortcuts import get_object_or_404
    
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    if not subscription_group:
        messages.error(request, 'You are not an admin of any active team subscription.')
        return redirect('accounts:manage_subscription')
    
    member = get_object_or_404(User, id=user_id)
    
    if member not in subscription_group.members.all():
        messages.error(request, 'This user is not a member of your team.')
        return redirect('accounts:manage_team')
    
    # Remove from subscription group
    subscription_group.members.remove(member)
    
    # Delete all grids for this member
    from pages.models import Project
    member_projects = Project.objects.filter(user=member)
    grids_deleted = member_projects.count()
    member_projects.delete()
    
    # Downgrade user to free
    member.tier = 'free'
    member.team_admin = None
    member.save(update_fields=['tier', 'team_admin'])
    
    # Update Stripe subscription metadata with new team info
    from accounts.stripe_django_views import update_subscription_metadata_with_team_info
    update_subscription_metadata_with_team_info(subscription_group)
    
    messages.success(request, f'{member.email} has been removed from your team. {grids_deleted} grid(s) have been deleted.')
    return redirect('accounts:manage_team')


@login_required
def cancel_team_subscription_view(request):
    """
    Cancel the team subscription - downgrades all members to free and deletes all their grids
    """
    from accounts.models import SubscriptionGroup
    from pages.models import Project
    import stripe
    import os
    
    if request.method != 'POST':
        return redirect('accounts:manage_team')
    
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    if not subscription_group:
        messages.error(request, 'You are not an admin of any active team subscription.')
        return redirect('accounts:manage_subscription')
    
    # Cancel Stripe subscription - cancel immediately (not at period end)
    if subscription_group.stripe_subscription_id:
        try:
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            # Cancel immediately
            stripe.Subscription.delete(subscription_group.stripe_subscription_id)
            logger.info(f"Stripe subscription {subscription_group.stripe_subscription_id} canceled immediately")
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            # Try cancel_at_period_end as fallback
            try:
                stripe.Subscription.modify(
                    subscription_group.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Stripe subscription {subscription_group.stripe_subscription_id} scheduled for cancellation at period end")
            except Exception as e2:
                logger.error(f"Error scheduling Stripe subscription cancellation: {e2}")
        except Exception as e:
            logger.error(f"Error canceling Stripe subscription: {e}")
    
    # Mark subscription group as inactive
    subscription_group.is_active = False
    subscription_group.save()
    
    # Delete all grids and downgrade all members to free (including admin, who is now a member)
    members = subscription_group.members.all()
    total_grids_deleted = 0
    
    for member in members:
        # Delete all projects (grids) for this member
        member_projects = Project.objects.filter(user=member)
        grids_deleted = member_projects.count()
        member_projects.delete()
        total_grids_deleted += grids_deleted
        
        # Downgrade member to free
        member.tier = 'free'
        member.team_admin = None
        member.save(update_fields=['tier', 'team_admin'])
    
    # If admin is not in members list (shouldn't happen with new logic, but handle edge case)
    if request.user not in members:
        admin_projects = Project.objects.filter(user=request.user)
        admin_grids_deleted = admin_projects.count()
        admin_projects.delete()
        total_grids_deleted += admin_grids_deleted
        
        # Downgrade admin to free
        request.user.tier = 'free'
        request.user.save(update_fields=['tier'])
    
    messages.success(request, f'Team subscription has been canceled. All {total_grids_deleted} grid(s) have been deleted and all members have been downgraded to Free.')
    return redirect('accounts:manage_subscription')


@login_required
def reduce_team_subscription_view(request):
    """
    Reduce team subscription by removing seats
    """
    from accounts.models import SubscriptionGroup
    import stripe
    import os
    
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    if request.method != 'POST':
        return redirect('accounts:manage_team')
    
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    if not subscription_group:
        messages.error(request, 'You are not an admin of any active team subscription.')
        return redirect('accounts:manage_subscription')
    
    # Get reduction quantity from form
    try:
        reduction_quantity = int(request.POST.get('reduction_quantity', 0))
        if reduction_quantity < 1:
            messages.error(request, 'Please enter a valid number of seats to remove.')
            return redirect('accounts:manage_team')
    except ValueError:
        messages.error(request, 'Invalid quantity. Please enter a valid number.')
        return redirect('accounts:manage_team')
    
    # Check current usage
    current_members_count = subscription_group.get_active_members_count()
    from accounts.models import TeamInvitation
    pending_count = TeamInvitation.objects.filter(
        subscription_group=subscription_group,
        status='pending'
    ).count()
    current_usage = current_members_count + pending_count
    
    # Calculate new quantity
    new_quantity = subscription_group.quantity - reduction_quantity
    
    # Validate new quantity
    if new_quantity < 1:
        messages.error(request, 'You must have at least 1 seat in your subscription.')
        return redirect('accounts:manage_team')
    
    # Allow reducing below current usage - user can manage members/invitations separately
    # This matches Stripe Portal behavior which allows quantity changes regardless of usage
    if new_quantity < current_usage:
        messages.warning(request, f'Warning: Reducing to {new_quantity} seats while you have {current_usage} in use ({current_members_count} active + {pending_count} pending). You may need to remove members or cancel invitations to free up seats.')
    
    # Update Stripe subscription
    if subscription_group.stripe_subscription_id:
        try:
            # Retrieve current subscription
            subscription = stripe.Subscription.retrieve(subscription_group.stripe_subscription_id)
            
            # Get the subscription item
            subscription_item_id = subscription['items']['data'][0]['id']
            current_quantity = subscription['items']['data'][0]['quantity']
            
            # Update subscription quantity in Stripe
            # The webhook will handle updating our database when Stripe confirms the change
            updated_subscription = stripe.Subscription.modify(
                subscription_group.stripe_subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'quantity': new_quantity,
                }],
                proration_behavior='always_invoice',  # Prorate the reduction
            )
            
            # Verify the update was successful by checking the returned subscription
            confirmed_quantity = updated_subscription['items']['data'][0]['quantity']
            if confirmed_quantity != new_quantity:
                logger.warning(f'Stripe subscription quantity mismatch: expected {new_quantity}, got {confirmed_quantity}')
            
            # Optimistically update our database (webhook will confirm)
            # This provides immediate feedback to the user
            subscription_group.quantity = confirmed_quantity
            subscription_group.save()
            
            messages.success(request, f'Successfully reduced subscription by {reduction_quantity} seat(s). Your subscription now has {confirmed_quantity} total seats.')
            logger.info(f'Team subscription reduced via Stripe API: {subscription_group.stripe_subscription_id} from {current_quantity} to {confirmed_quantity} seats (reduction: {reduction_quantity})')
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error reducing team subscription: {e}")
            messages.error(request, 'There was an error updating your subscription. Please contact support.')
        except Exception as e:
            logger.error(f"Error reducing team subscription: {e}", exc_info=True)
            messages.error(request, 'An unexpected error occurred. Please contact support.')
    else:
        messages.error(request, 'No Stripe subscription found. Please contact support.')
    
    return redirect('accounts:manage_team')


@login_required
def upgrade_team_subscription_view(request):
    """
    Upgrade team subscription by adding more seats
    """
    from accounts.models import SubscriptionGroup
    import stripe
    import os
    
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    if request.method != 'POST':
        return redirect('accounts:manage_team')
    
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    if not subscription_group:
        messages.error(request, 'You are not an admin of any active team subscription.')
        return redirect('accounts:manage_subscription')
    
    # Get additional quantity from form
    try:
        additional_quantity = int(request.POST.get('additional_quantity', 0))
        if additional_quantity < 1:
            messages.error(request, 'Please enter a valid number of additional seats.')
            return redirect('accounts:manage_team')
    except ValueError:
        messages.error(request, 'Invalid quantity. Please enter a valid number.')
        return redirect('accounts:manage_team')
    
    # Update Stripe subscription
    if subscription_group.stripe_subscription_id:
        try:
            # Retrieve current subscription
            subscription = stripe.Subscription.retrieve(subscription_group.stripe_subscription_id)
            
            # Get the subscription item
            subscription_item_id = subscription['items']['data'][0]['id']
            current_quantity = subscription['items']['data'][0]['quantity']
            new_quantity = current_quantity + additional_quantity
            
            # Update subscription quantity
            stripe.Subscription.modify(
                subscription_group.stripe_subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'quantity': new_quantity,
                }],
                proration_behavior='always_invoice',  # Charge immediately for the additional seats
            )
            
            # Update subscription group quantity
            subscription_group.quantity = new_quantity
            subscription_group.save()
            
            messages.success(request, f'Successfully added {additional_quantity} seat(s). Your subscription now has {new_quantity} total seats.')
            logger.info(f'Team subscription upgraded: {subscription_group.stripe_subscription_id} from {current_quantity} to {new_quantity} seats')
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error upgrading team subscription: {e}")
            messages.error(request, 'There was an error updating your subscription. Please contact support.')
        except Exception as e:
            logger.error(f"Error upgrading team subscription: {e}", exc_info=True)
            messages.error(request, 'An unexpected error occurred. Please contact support.')
    else:
        messages.error(request, 'No Stripe subscription found. Please contact support.')
    
    return redirect('accounts:manage_team')


@login_required
def transfer_team_admin_view(request, user_id):
    """
    Transfer admin role to another team member
    """
    from accounts.models import SubscriptionGroup
    from django.shortcuts import get_object_or_404
    
    if request.method != 'POST':
        return redirect('accounts:manage_team')
    
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    if not subscription_group:
        messages.error(request, 'You are not an admin of any active team subscription.')
        return redirect('accounts:manage_subscription')
    
    # Check if admin is the only member - cannot transfer if so
    members_count = subscription_group.members.count()
    if members_count <= 1:
        messages.error(request, 'Cannot transfer admin role. You are the only member of the team.')
        return redirect('accounts:manage_team')
    
    new_admin = get_object_or_404(User, id=user_id)
    
    if new_admin not in subscription_group.members.all():
        messages.error(request, 'This user is not a member of your team.')
        return redirect('accounts:manage_team')
    
    # Prevent transferring to yourself
    if new_admin == request.user:
        messages.error(request, 'You cannot transfer admin role to yourself.')
        return redirect('accounts:manage_team')
    
    # Transfer admin
    subscription_group.admin = new_admin
    subscription_group.save()
    
    # Update team_admin for all members (including the old admin, who remains a member)
    for member in subscription_group.members.all():
        member.team_admin = new_admin
        member.save(update_fields=['team_admin'])
    
    messages.success(request, f'Admin role has been transferred to {new_admin.email}.')
    return redirect('accounts:manage_subscription')


@login_required
def cancel_team_invitation_view(request, invitation_id):
    """
    Cancel a pending team invitation
    """
    if request.method != 'POST':
        return redirect('accounts:account_settings')
    
    from accounts.models import TeamInvitation
    from django.shortcuts import get_object_or_404
    
    invitation = get_object_or_404(TeamInvitation, id=invitation_id)
    
    # Verify the invitation belongs to a subscription group where user is admin
    if invitation.subscription_group.admin != request.user:
        messages.error(request, 'You do not have permission to cancel this invitation.')
        return redirect('accounts:account_settings')
    
    # Only allow canceling pending invitations
    if invitation.status != 'pending':
        messages.error(request, 'This invitation cannot be canceled.')
        return redirect('accounts:account_settings')
    
    # Mark invitation as declined
    invitation.status = 'declined'
    invitation.save()
    
    # Update Stripe subscription metadata with new team info
    from accounts.stripe_django_views import update_subscription_metadata_with_team_info
    update_subscription_metadata_with_team_info(invitation.subscription_group)
    
    messages.success(request, f'Invitation to {invitation.invited_email} has been canceled.')
    
    # Redirect back to the page they came from, or account settings
    referer = request.META.get('HTTP_REFERER')
    if referer and 'manage-team' in referer:
        return redirect('accounts:manage_team')
    return redirect('accounts:account_settings')


def accept_team_invitation_view(request, token):
    """
    Accept a team invitation - shows password setup form for new users or accepts for existing users
    """
    from accounts.models import TeamInvitation
    from django.shortcuts import get_object_or_404
    from django.contrib.auth import login
    
    invitation = get_object_or_404(TeamInvitation, token=token)
    
    if not invitation.can_be_accepted():
        messages.error(request, 'This invitation has expired or is no longer valid.')
        return redirect('pages:project_list')
    
    # Check if user already exists with this email
    try:
        existing_user = User.objects.get(email=invitation.invited_email)
        
        # If user is logged in and email matches
        if request.user.is_authenticated:
            if request.user.email == invitation.invited_email:
                if request.method == 'POST':
                    # Accept the invitation
                    if invitation.accept(user=request.user):
                        # Set team_admin
                        request.user.team_admin = invitation.subscription_group.admin
                        request.user.save(update_fields=['team_admin'])
                        # Update Stripe subscription metadata with new team info
                        from accounts.stripe_django_views import update_subscription_metadata_with_team_info
                        update_subscription_metadata_with_team_info(invitation.subscription_group)
                        # Don't show success message - redirect silently
                        return redirect('pages:project_list')
                    else:
                        messages.error(request, 'Unable to accept invitation. The team may be full.')
                        return redirect('pages:project_list')
                else:
                    # Show invitation details page for existing user
                    admin_name = invitation.invited_by.get_full_name() or invitation.invited_by.email
                    admin_email = invitation.invited_by.email
                    context = {
                        'invitation': invitation,
                        'admin_name': admin_name,
                        'admin_email': admin_email,
                        'existing_user': True,
                    }
                    return render(request, 'accounts/pages/team/accept_invitation.html', context)
            else:
                messages.error(request, 'This invitation is for a different email address.')
                return redirect('pages:project_list')
        else:
            # User exists but not logged in - redirect to login
            request.session['team_invitation_token'] = token
            messages.info(request, 'Please log in to accept this invitation.')
            return redirect('accounts:login')
    
    except User.DoesNotExist:
        # User doesn't exist - show password setup form
        form = TeamInvitationAcceptanceForm()
        
        if request.method == 'POST':
            form = TeamInvitationAcceptanceForm(request.POST)
            if form.is_valid():
                # Check if team has available seats before creating user
                if not invitation.subscription_group.has_available_seats():
                    messages.error(request, 'Unable to accept invitation. The team is full.')
                    return redirect('pages:project_list')
                
                # Create the user
                user = User.objects.create_user(
                    email=invitation.invited_email,
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    tier='pro',  # Set to Team Toad (pro) tier
                    email_verified=True,  # Auto-verify since they came from invitation
                )
                
                # Accept the invitation and add to subscription group
                if invitation.accept(user=user):
                    # Set team_admin (invitation.accept already sets tier to pro, but ensure team_admin is set)
                    user.team_admin = invitation.subscription_group.admin
                    user.save(update_fields=['team_admin'])
                    
                    # Update Stripe subscription metadata with new team info
                    from accounts.stripe_django_views import update_subscription_metadata_with_team_info
                    update_subscription_metadata_with_team_info(invitation.subscription_group)
                    
                    # Log the user in
                    login(request, user)
                    
                    # Don't show success message - redirect silently
                    return redirect('pages:project_list')
                else:
                    # If invitation accept fails, delete the user and show error
                    user.delete()
                    messages.error(request, 'Unable to accept invitation. The team may be full.')
                    return redirect('pages:project_list')
        
        # Show password setup form
        admin_name = invitation.invited_by.get_full_name() or invitation.invited_by.email
        admin_email = invitation.invited_by.email
        context = {
            'invitation': invitation,
            'form': form,
            'admin_name': admin_name,
            'admin_email': admin_email,
            'existing_user': False,
        }
        return render(request, 'accounts/pages/team/accept_invitation.html', context)


def beta_feedback_email_preview(request):
    """Preview the beta feedback email template"""
    from django.template.loader import render_to_string
    from django.contrib.auth import get_user_model
    from django.http import HttpResponse
    from django.utils import timezone
    
    User = get_user_model()
    
    # Use current logged in user if available, otherwise create test user
    if request.user.is_authenticated:
        test_user = request.user
    else:
        test_user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
    
    # Render the beta feedback email template
    beta_feedback_html = render_to_string('accounts/email/beta_feedback_email.html', {
        'user': test_user,
        'now': timezone.now(),
    })
    
    # Return the rendered HTML directly
    return HttpResponse(beta_feedback_html)