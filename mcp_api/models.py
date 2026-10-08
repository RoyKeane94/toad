import hashlib
import hmac
import secrets

from django.conf import settings
from django.db import models


TOKEN_PREFIX = 'toad_'


def generate_personal_access_token():
    """Return a new plaintext token. Store only the hash."""
    return f'{TOKEN_PREFIX}{secrets.token_urlsafe(32)}'


def hash_personal_access_token(raw_token):
    """Hash a token with the Django secret so a DB leak is not enough on its own."""
    return hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        raw_token.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


class PersonalAccessToken(models.Model):
    """One Grok Bot token per user. The plaintext value is shown only at creation."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mcp_access_token',
    )
    token_prefix = models.CharField(max_length=16, help_text='First characters shown in settings.')
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['token_hash']),
        ]

    def __str__(self):
        return f'{self.user.email} ({self.token_prefix}…)'

    @classmethod
    def issue_for_user(cls, user):
        """Create or replace the user's token and return the plaintext value."""
        raw_token = generate_personal_access_token()
        token_hash = hash_personal_access_token(raw_token)
        prefix = raw_token[:12]
        cls.objects.filter(user=user).delete()
        cls.objects.create(user=user, token_prefix=prefix, token_hash=token_hash)
        return raw_token

    @classmethod
    def authenticate(cls, raw_token):
        """Return the user for a valid token, or None. Updates last_used_at."""
        if not raw_token:
            return None
        token_hash = hash_personal_access_token(raw_token)
        token = cls.objects.select_related('user').filter(token_hash=token_hash).first()
        if not token or not token.user.is_active:
            return None
        from django.utils import timezone
        token.last_used_at = timezone.now()
        token.save(update_fields=['last_used_at'])
        return token.user


class MCPRequestLog(models.Model):
    """Who asked, what they asked, when, and whether a follow-up is needed. No output stored."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mcp_request_logs',
    )
    asked_by = models.CharField(max_length=200, help_text='Who made the request.')
    request_text = models.TextField(help_text='What was asked.')
    follow_up_needed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['follow_up_needed', '-created_at']),
        ]

    def __str__(self):
        return f'{self.asked_by} @ {self.created_at:%Y-%m-%d %H:%M}'
