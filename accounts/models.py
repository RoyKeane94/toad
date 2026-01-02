from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from CRM.models import SocietyLink, SocietyUniversity

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of username.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    
    TIER_CHOICES = [
        ('free', 'Free'),
        ('personal', 'Personal'),
        ('personal_trial', 'Personal Trial'),
        ('personal_3_month_trial', 'Personal 3 Month Trial'),
        ('pro', 'Team Toad'),
        ('pro_trial', 'Team Toad Trial'),
        ('society_pro', 'Society Team Toad'),
        ('beta', 'Beta'),
    ]
    
    username = None  # Remove username field
    email = models.EmailField(unique=True, help_text='Required. Enter a valid email address.')
    first_name = models.CharField(max_length=30, help_text='Required. Enter your first name.')
    last_name = models.CharField(max_length=30, blank=True, help_text='Optional. Enter your last name.')
    tier = models.CharField(max_length=35, choices=TIER_CHOICES, default='beta',blank=True)
    team_admin = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='team_members', help_text='Admin user if this user is part of a team subscription.')
    associated_society = models.ForeignKey(SocietyLink, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    associated_university = models.ForeignKey(SocietyUniversity, on_delete=models.CASCADE, null=True, blank=True)
    second_grid_created = models.BooleanField(default=False, help_text='Whether the user has created their second grid.')
    regular_user = models.BooleanField(default=False, help_text='Whether the user is a regular user.')
    email_subscribed = models.BooleanField(default=True, help_text='Whether the user has subscribed to the email list.')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe customer ID for billing portal access.')
    
    # Trial and billing fields
    trial_started_at = models.DateTimeField(null=True, blank=True, help_text='When the user started their trial period.')
    trial_ends_at = models.DateTimeField(null=True, blank=True, help_text='When the user trial period ends.')
    trial_type = models.CharField(max_length=20, choices=[
        ('1_month', '1 Month'),
        ('3_month', '3 Month'),
        ('6_month', '6 Month'),
    ], null=True, blank=True, help_text='Type of trial period for Pro users.')
    
    # Security and tracking fields
    email_verified = models.BooleanField(default=False, help_text='Whether the user has verified their email address.')
    email_verification_token = models.CharField(max_length=100, null=True, blank=True, help_text='Token for email verification.')
    email_verification_sent_at = models.DateTimeField(null=True, blank=True, help_text='When the verification email was sent.')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, help_text='IP address of last login.')
    failed_login_attempts = models.PositiveIntegerField(default=0, help_text='Number of consecutive failed login attempts.')
    account_locked_until = models.DateTimeField(null=True, blank=True, help_text='Account locked until this time.')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']  # Fields required when creating superuser (email is already included)

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        """
        Return the short name for the user.
        """
        return self.first_name
    
    def trial_status(self):
        """
        Return trial status information for admin display.
        """
        if not self.trial_ends_at:
            return "No trial"
        
        from django.utils import timezone
        now = timezone.now()
        
        if now < self.trial_ends_at:
            days_left = (self.trial_ends_at - now).days
            return f"Active ({days_left} days left)"
        else:
            return "Expired"
    
    trial_status.short_description = "Trial Status"
    
    def is_on_trial(self):
        """Check if user is currently on trial"""
        if not self.trial_ends_at:
            return False
        from django.utils import timezone
        return timezone.now() < self.trial_ends_at
    
    def has_trial_expired(self):
        """Check if user's trial has expired"""
        if not self.trial_ends_at:
            return False
        from django.utils import timezone
        return timezone.now() >= self.trial_ends_at
    
    def start_trial(self, days=180):  # 6 months = ~180 days
        """Start a trial period for the user"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.trial_started_at = timezone.now()
        self.trial_ends_at = timezone.now() + timedelta(days=days)
        self.tier = 'personal_trial'  # Give them Personal features during trial
        self.save()
    
    def start_pro_trial(self, days=90):  # 3 months = ~90 days
        """Start a Pro trial period for the user"""
        from django.utils import timezone
        from datetime import timedelta
        
        self.trial_started_at = timezone.now()
        self.trial_ends_at = timezone.now() + timedelta(days=days)
        self.tier = 'pro_trial'  # Give them Pro features during trial
        self.save()
    
    def is_account_locked(self):
        """
        Check if the account is currently locked due to failed login attempts.
        """
        if self.account_locked_until:
            from django.utils import timezone
            return timezone.now() < self.account_locked_until
        return False
    
    def reset_failed_attempts(self):
        """
        Reset failed login attempts and unlock account.
        """
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    
    def increment_failed_attempts(self):
        """
        Increment failed login attempts and lock account if threshold reached.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        self.failed_login_attempts += 1
        
        # Lock account for 30 minutes after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    
    def generate_email_verification_token(self):
        """
        Generate a secure token for email verification.
        """
        import secrets
        import string
        from django.utils import timezone
        
        # Generate a 32-character random token
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        self.email_verification_token = token
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        
        return token
    
    def verify_email_token(self, token):
        """
        Verify the email verification token and mark email as verified.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if token matches and is not expired (24 hours)
        if (self.email_verification_token == token and 
            self.email_verification_sent_at and 
            timezone.now() < self.email_verification_sent_at + timedelta(hours=24)):
            
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_sent_at = None
            self.save(update_fields=['email_verified', 'email_verification_token', 'email_verification_sent_at'])
            return True
        
        return False
    
    def generate_password_reset_token(self):
        """
        Generate a secure token for password reset.
        """
        import secrets
        import string
        from django.utils import timezone
        
        # Generate a 32-character random token
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        self.email_verification_token = token  # Reuse the same field
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        
        return token
    
    def verify_password_reset_token(self, token):
        """
        Verify the password reset token.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if token matches and is not expired (1 hour)
        if (self.email_verification_token == token and 
            self.email_verification_sent_at and 
            timezone.now() < self.email_verification_sent_at + timedelta(hours=1)):
            
            return True
        
        return False
    
    def clear_password_reset_token(self):
        """
        Clear the password reset token after use.
        """
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
    
    def has_created_second_grid(self):
        """
        Check if user has created their second grid.
        Uses the cached boolean field for optimal performance.
        """
        return self.second_grid_created


class SubscriptionGroup(models.Model):
    """
    Represents a team subscription group where an admin pays for multiple Pro subscriptions.
    """
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_subscription_groups', help_text='The admin user who manages this subscription group.')
    members = models.ManyToManyField(User, related_name='subscription_groups', blank=True, help_text='Team members in this subscription group.')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe subscription ID for this team subscription.')
    quantity = models.PositiveIntegerField(default=1, help_text='Number of subscriptions purchased.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text='Whether this subscription group is active.')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', 'is_active']),
            models.Index(fields=['stripe_subscription_id']),
        ]
    
    def __str__(self):
        return f"Team Subscription - Admin: {self.admin.email} ({self.quantity} seats)"
    
    def get_active_members_count(self):
        """Get the number of active members in this group."""
        return self.members.filter(is_active=True).count()
    
    def has_available_seats(self):
        """Check if there are available seats for new members."""
        return self.get_active_members_count() < self.quantity


class TeamInvitation(models.Model):
    """
    Tracks email invitations for team members to join a subscription group.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    subscription_group = models.ForeignKey(SubscriptionGroup, on_delete=models.CASCADE, related_name='invitations', help_text='The subscription group this invitation is for.')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_team_invitations', help_text='The admin who sent this invitation.')
    invited_email = models.EmailField(help_text='Email address of the invited user.')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_team_invitations', null=True, blank=True, help_text='User object if they have an account.')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', help_text='Status of the invitation.')
    token = models.CharField(max_length=32, unique=True, help_text='Unique token for the invitation.')
    expires_at = models.DateTimeField(help_text='When the invitation expires.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True, help_text='When the invitation was accepted.')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['invited_email', 'status']),
            models.Index(fields=['subscription_group', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Team Invitation - {self.invited_email} ({self.status})"
    
    def generate_token(self):
        """Generate a secure random token for the invitation."""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if the invitation has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_be_accepted(self):
        """Check if the invitation can still be accepted."""
        return self.status == 'pending' and not self.is_expired()
    
    def accept(self, user=None):
        """Accept the invitation and add user to the subscription group.
        Also verifies the user's email since clicking the invitation link acts as verification.
        """
        if not self.can_be_accepted():
            return False
        
        # Check if there are available seats
        if not self.subscription_group.has_available_seats():
            return False
        
        # For existing users, use the provided user
        if user:
            self.invited_user = user
        # For new users, try to find by email
        elif not self.invited_user and self.invited_email:
            try:
                self.invited_user = User.objects.get(email=self.invited_email)
            except User.DoesNotExist:
                pass
        
        # Add user to the subscription group
        if self.invited_user:
            self.subscription_group.members.add(self.invited_user)
            # Set user tier to pro and verify their email
            # (clicking invitation link acts as email verification)
            self.invited_user.tier = 'pro'
            self.invited_user.email_verified = True
            self.invited_user.email_verification_token = None
            self.invited_user.email_verification_sent_at = None
            self.invited_user.save(update_fields=['tier', 'email_verified', 'email_verification_token', 'email_verification_sent_at'])
        
        # Update invitation status
        from django.utils import timezone
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        return True

