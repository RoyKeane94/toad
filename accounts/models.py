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

