import hashlib
import hmac
import json
import secrets
from datetime import timezone as dt_timezone

from django.conf import settings
from django.db import models
from django.utils import timezone


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


def user_has_agent_access(user):
    """True when the user has at least one active (non-revoked) personal access token."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    if not getattr(user, 'is_active', True):
        return False
    return PersonalAccessToken.objects.filter(user=user).exists()


class DecisionEntry(models.Model):
    """Append-only record of what an agent was asked, what it decided, and why."""

    STATUS_PENDING = 'pending_review'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_SUPERSEDED = 'superseded'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_SUPERSEDED, 'Superseded'),
    ]
    REVIEW_STATUSES = {STATUS_APPROVED, STATUS_REJECTED, STATUS_SUPERSEDED}
    MUTABLE_FIELDS = {'status', 'reviewer', 'reviewed_at', 'review_comment'}

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='decision_entries',
    )
    created_at = models.DateTimeField(default=timezone.now)
    grid = models.ForeignKey(
        'pages.Project',
        on_delete=models.CASCADE,
        related_name='decision_entries',
    )
    task = models.ForeignKey(
        'pages.Task',
        on_delete=models.SET_NULL,
        related_name='decision_entries',
        null=True,
        blank=True,
    )
    task_id_snapshot = models.IntegerField(null=True, blank=True)
    task_text_snapshot = models.TextField(blank=True, default='')
    agent_name = models.CharField(max_length=100)
    token = models.ForeignKey(
        PersonalAccessToken,
        on_delete=models.SET_NULL,
        related_name='decision_entries',
        null=True,
        blank=True,
    )
    requested_by = models.CharField(max_length=200)
    request = models.CharField(max_length=500, help_text='What was asked, one line.')
    action_summary = models.TextField()
    decision = models.TextField()
    rationale = models.TextField(blank=True, default='')
    sources = models.JSONField(default=list, blank=True)
    output_link = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewer = models.CharField(max_length=200, blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True, default='')
    supersedes = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='superseded_by',
        null=True,
        blank=True,
    )
    prev_hash = models.CharField(max_length=64, blank=True, default='')
    entry_hash = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['grid', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['agent_name', '-created_at']),
        ]
        verbose_name_plural = 'decision entries'

    def __str__(self):
        return f'{self.agent_name}: {self.decision[:60]}'

    def canonical_payload(self):
        created_at = self.created_at
        if timezone.is_aware(created_at):
            created_at = created_at.astimezone(dt_timezone.utc)
        return {
            'id': self.id,
            'created_at': created_at.isoformat(),
            'grid_id': self.grid_id,
            'task_id_snapshot': self.task_id_snapshot,
            'task_text_snapshot': self.task_text_snapshot,
            'agent_name': self.agent_name,
            'requested_by': self.requested_by,
            'request': self.request,
            'action_summary': self.action_summary,
            'decision': self.decision,
            'rationale': self.rationale,
            'sources': self.sources or [],
            'output_link': self.output_link or '',
            'supersedes_id': self.supersedes_id,
            'prev_hash': self.prev_hash,
        }

    def compute_hash(self):
        payload = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous is not None:
                for field in self._meta.concrete_fields:
                    name = field.attname
                    if name == 'id' or name in self.MUTABLE_FIELDS:
                        continue
                    if name == 'entry_hash' and not previous.entry_hash:
                        continue
                    if getattr(previous, name) != getattr(self, name):
                        raise ValueError('Decision entries are append-only')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Decision entries cannot be deleted')


class DecisionReview(models.Model):
    """Immutable record of a human (or superseding agent) changing a decision's status."""

    entry = models.ForeignKey(
        DecisionEntry,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    actor = models.CharField(max_length=200)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['entry', 'created_at']),
        ]

    def __str__(self):
        return f'{self.actor}: {self.old_status} → {self.new_status}'

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Decision reviews cannot be edited')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Decision reviews cannot be deleted')
