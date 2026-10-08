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
    """Named agent token. Each agent (Ramble, Research, Grok Bot) should have its own."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mcp_access_tokens',
    )
    name = models.CharField(max_length=100, default='Grok Bot', help_text='Agent name recorded on the activity log.')
    token_prefix = models.CharField(max_length=16, help_text='First characters shown in settings.')
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['user', 'name']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_mcp_token_name_per_user'),
        ]

    def __str__(self):
        return f'{self.user.email} / {self.name} ({self.token_prefix}…)'

    @classmethod
    def issue_for_user(cls, user, name='Grok Bot'):
        """Create or replace the token for this agent name and return the plaintext value."""
        name = (name or '').strip() or 'Grok Bot'
        raw_token = generate_personal_access_token()
        token_hash = hash_personal_access_token(raw_token)
        prefix = raw_token[:12]
        cls.objects.filter(user=user, name=name).delete()
        cls.objects.create(user=user, name=name, token_prefix=prefix, token_hash=token_hash)
        return raw_token

    @classmethod
    def authenticate_token(cls, raw_token):
        """Return the token for a valid value, or None. Updates last_used_at."""
        if not raw_token:
            return None
        token_hash = hash_personal_access_token(raw_token)
        token = cls.objects.select_related('user').filter(token_hash=token_hash).first()
        if not token or not token.user.is_active:
            return None
        from django.utils import timezone
        token.last_used_at = timezone.now()
        token.save(update_fields=['last_used_at'])
        return token

    @classmethod
    def authenticate(cls, raw_token):
        """Return the user for a valid token, or None."""
        token = cls.authenticate_token(raw_token)
        return token.user if token else None


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


class TaskActivity(models.Model):
    """Agent, action, task and time. Undo can be added later."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_activities',
    )
    project = models.ForeignKey(
        'pages.Project',
        on_delete=models.CASCADE,
        related_name='task_activities',
        null=True,
        blank=True,
    )
    task = models.ForeignKey(
        'pages.Task',
        on_delete=models.SET_NULL,
        related_name='activities',
        null=True,
        blank=True,
    )
    agent = models.CharField(max_length=100, help_text='Token / agent name that made the change.')
    action = models.CharField(max_length=200)
    task_text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name_plural = 'task activities'

    def __str__(self):
        return f'{self.agent} {self.action} {self.task_text[:40]}'
