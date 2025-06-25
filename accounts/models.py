from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

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
    """
    Custom User model that uses email as the unique identifier
    and includes first_name as a required field for registration.
    """
    username = None  # Remove username field
    email = models.EmailField(unique=True, help_text='Required. Enter a valid email address.')
    first_name = models.CharField(max_length=30, help_text='Required. Enter your first name.')
    last_name = models.CharField(max_length=30, blank=True, help_text='Optional. Enter your last name.')
    
    # Security and tracking fields
    email_verified = models.BooleanField(default=False, help_text='Whether the user has verified their email address.')
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
