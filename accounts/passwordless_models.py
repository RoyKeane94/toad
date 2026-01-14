"""
Passwordless Login Models
=========================
Secure model for storing email-based login codes.
"""
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
import secrets
import hashlib
from datetime import timedelta

User = get_user_model()


class LoginCode(models.Model):
    """
    Stores one-time login codes for passwordless authentication.
    Codes are hashed before storage for security.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_codes')
    code_hash = models.CharField(max_length=64, help_text='SHA-256 hash of the login code')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text='Code expiration time')
    used_at = models.DateTimeField(null=True, blank=True, help_text='When the code was used')
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='IP address that requested the code')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'expires_at']),
            models.Index(fields=['code_hash', 'expires_at']),
        ]
    
    @staticmethod
    def generate_code(length=6):
        """
        Generate a secure numeric code.
        Default is 6 digits for easy entry.
        """
        return ''.join(secrets.choice('0123456789') for _ in range(length))
    
    @staticmethod
    def hash_code(code):
        """Hash a code using SHA-256."""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @classmethod
    def create_for_user(cls, user, ip_address=None, code_length=6, expiry_minutes=10):
        """
        Create a new login code for a user.
        
        Args:
            user: User instance
            ip_address: IP address of the request
            code_length: Length of code (default 6 digits)
            expiry_minutes: Minutes until code expires (default 10)
        
        Returns:
            tuple: (LoginCode instance, plain_text_code)
        """
        # Generate code
        plain_code = cls.generate_code(code_length)
        code_hash = cls.hash_code(plain_code)
        
        # Set expiration
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        
        # Create and save
        login_code = cls.objects.create(
            user=user,
            code_hash=code_hash,
            expires_at=expires_at,
            ip_address=ip_address
        )
        
        return login_code, plain_code
    
    def verify_code(self, code):
        """
        Verify if a code matches and is still valid.
        Returns True if valid, False otherwise.
        """
        # Check if already used
        if self.used_at:
            return False
        
        # Check if expired
        if timezone.now() > self.expires_at:
            return False
        
        # Verify code hash
        code_hash = self.hash_code(code)
        if code_hash != self.code_hash:
            return False
        
        # Mark as used
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])
        
        return True
    
    @classmethod
    def get_valid_code(cls, user, code):
        """
        Find and verify a code for a user.
        Returns LoginCode instance if valid, None otherwise.
        """
        # Clean up expired codes first
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
        
        # Find unused codes for this user
        valid_codes = cls.objects.filter(
            user=user,
            used_at__isnull=True,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')
        
        # Try to verify against each code
        for login_code in valid_codes:
            if login_code.verify_code(code):
                return login_code
        
        return None
    
    @classmethod
    def check_rate_limit(cls, email, ip_address=None):
        """
        Check if user has exceeded rate limit for code requests.
        Limits: 3 codes per 15 minutes per email/IP.
        
        Returns:
            tuple: (allowed: bool, remaining_seconds: int)
        """
        cache_key_email = f'login_code_rate_limit_email_{email}'
        cache_key_ip = f'login_code_rate_limit_ip_{ip_address}' if ip_address else None
        
        # Check email rate limit
        email_count = cache.get(cache_key_email, 0)
        if email_count >= 3:
            # Get remaining time
            remaining = cache.ttl(cache_key_email)
            return False, remaining if remaining else 0
        
        # Check IP rate limit if provided
        if cache_key_ip:
            ip_count = cache.get(cache_key_ip, 0)
            if ip_count >= 5:  # Higher limit for IP (multiple users)
                remaining = cache.ttl(cache_key_ip)
                return False, remaining if remaining else 0
        
        return True, 0
    
    @classmethod
    def record_code_request(cls, email, ip_address=None):
        """
        Record a code request for rate limiting.
        """
        cache_key_email = f'login_code_rate_limit_email_{email}'
        cache_key_ip = f'login_code_rate_limit_ip_{ip_address}' if ip_address else None
        
        # Increment email counter (15 minute window)
        email_count = cache.get(cache_key_email, 0)
        cache.set(cache_key_email, email_count + 1, 900)  # 15 minutes
        
        # Increment IP counter if provided
        if cache_key_ip:
            ip_count = cache.get(cache_key_ip, 0)
            cache.set(cache_key_ip, ip_count + 1, 900)  # 15 minutes

