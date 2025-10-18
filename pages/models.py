from django.db import models
from accounts.models import User  # Use our custom User model
from django.urls import reverse
import secrets
import string
from django.db.models.signals import post_save
from django.dispatch import receiver

class ProjectGroup(models.Model):
    name = models.CharField(max_length=100)
    is_team_toad = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']  # Order by name
        indexes = [
            models.Index(fields=['is_team_toad']),  # For team toad project group queries
        ]
    
class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='toad_projects')
    name = models.CharField(max_length=100)
    is_team_toad = models.BooleanField(default=False)
    team_toad_user = models.ManyToManyField(User, related_name='team_toad_projects', null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)  # For maintaining project order within groups
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Check if is_team_toad is being set to True
        if self.is_team_toad and self.pk:
            # Get the current state from the database
            try:
                old_instance = Project.objects.get(pk=self.pk)
                if not old_instance.is_team_toad:
                    # is_team_toad was just set to True, add the user to team
                    self.team_toad_user.add(self.user)
            except Project.DoesNotExist:
                # New instance, add user if is_team_toad is True
                if self.is_team_toad:
                    self.team_toad_user.add(self.user)
        elif self.is_team_toad and not self.pk:
            # New instance with is_team_toad=True, add user after save
            super().save(*args, **kwargs)
            self.team_toad_user.add(self.user)
            return
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['project_group', 'order', '-created_at']  # Order by group, then by order, then by creation time
        indexes = [
            models.Index(fields=['user', '-created_at']),  # For user's project list
            models.Index(fields=['user', 'id']),  # For project access checks
            models.Index(fields=['user', 'project_group', 'order']),  # For ordered project queries within groups
            models.Index(fields=['user', 'is_archived']),  # For filtering user's active/archived projects
            models.Index(fields=['is_archived', 'project_group', 'order']),  # For team grid queries
            models.Index(fields=['is_team_toad', 'is_archived']),  # For team grid filtering
        ]

class RowHeader(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='row_headers')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0) # For maintaining row order
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - Row: {self.name}"

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'order']),  # For ordered row queries
        ]

class ColumnHeader(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='column_headers')
    name = models.CharField(max_length=100)
    is_category_column = models.BooleanField(default=False) # To identify the first "Time / Category" like column
    order = models.PositiveIntegerField(default=0) # For maintaining column order
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - Col: {self.name}"

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'is_category_column', 'order']),  # For ordered column queries
        ]

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    row_header = models.ForeignKey(RowHeader, on_delete=models.CASCADE, related_name='tasks')
    column_header = models.ForeignKey(ColumnHeader, on_delete=models.CASCADE, related_name='tasks')
    text = models.TextField(blank=False, null=False, help_text='Enter the task description')
    completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)  # For maintaining task order within cells
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reminder = models.DateTimeField(blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)

    def __str__(self):
        return f"{self.text[:50]} - {self.created_at} - project: {self.project.name} - user: {self.project.user}" if self.text else 'Empty Task'
    
    def clean(self):
        if not self.text or not self.text.strip():
            from django.core.exceptions import ValidationError
            raise ValidationError({'text': 'Task text cannot be empty.'})
    
    def has_reminder(self):
        """Check if task has a reminder set"""
        return self.reminder is not None
    
    def get_reminder_date_display(self):
        """Get formatted reminder date for display"""
        if self.reminder:
            return self.reminder.strftime('%d %b %Y')
        return None

    class Meta:
        ordering = ['order', 'created_at']  # Order first, then by creation time
        indexes = [
            models.Index(fields=['project', 'row_header', 'column_header']),  # For cell-based task queries
            models.Index(fields=['project', 'completed']),  # For completed task filtering
            models.Index(fields=['project', 'order']),  # For task ordering
            models.Index(fields=['project', 'row_header', 'column_header', 'order']),  # For ordered task queries
        ]

class TaskNote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')
    note = models.TextField(blank=False, null=False, help_text='Enter the note')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_task_notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task.text[:50]} - {self.created_at} - user: {self.task.project.user}" if self.note else 'Empty Note'
    
    class Meta:
        ordering = ['-created_at']  # Most recent first

class PersonalTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_templates')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class TeamToadTemplate(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_toad_templates')
    name = models.CharField(max_length=100)
    team_members = models.ManyToManyField(User, related_name='member_of_team_toad_templates', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['creator']),  # For creator's team toad template queries
        ]

class TemplateRowHeader(models.Model):
    template = models.ForeignKey(PersonalTemplate, on_delete=models.CASCADE, related_name='row_headers')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['template', 'order']

    def __str__(self):
        return f"{self.template.name} - {self.name}"

class TemplateColumnHeader(models.Model):
    template = models.ForeignKey(PersonalTemplate, on_delete=models.CASCADE, related_name='column_headers')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['template', 'order']

    def __str__(self):
        return f"{self.template.name} - {self.name}"
    
class TemplateTask(models.Model):
    template_row_header = models.ForeignKey(TemplateRowHeader, on_delete=models.CASCADE, related_name='tasks')
    template_column_header = models.ForeignKey(TemplateColumnHeader, on_delete=models.CASCADE, related_name='tasks')
    text = models.TextField(blank=False, null=False, help_text='Enter the task description')
    completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)  # For maintaining task order within cells
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['template_row_header', 'template_column_header', 'order']

    def __str__(self):
        return f"{self.text[:50]} - {self.created_at} - template: {self.template_row_header.template.name} - user: {self.template_row_header.template.user}" if self.text else 'Empty Task'
    
    def clean(self):
        if not self.text or not self.text.strip():
            from django.core.exceptions import ValidationError
            raise ValidationError({'text': 'Task text cannot be empty.'})

class ContactSubmission(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General Question'),
        ('bug_report', 'Bug Report'),
        ('feature_request', 'Feature Request'),
        ('account_help', 'Account Help'),
        ('technical_support', 'Technical Support'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, 
                           help_text="Associated user if they were logged in")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject}"

class GridInvitation(models.Model):
    """
    Model to track grid sharing invitations via email and shareable links
    """
    INVITATION_TYPE_CHOICES = [
        ('email', 'Email Invitation'),
        ('link', 'Shareable Link'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_email = models.EmailField(blank=True, help_text='Email address of the invited user (empty for shareable links)')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations', 
                                   null=True, blank=True, help_text='User object if they have an account')
    invitation_type = models.CharField(max_length=10, choices=INVITATION_TYPE_CHOICES, default='email')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=32, unique=True, help_text='Unique token for the invitation')
    personal_message = models.TextField(blank=True, help_text='Optional personal message from the inviter')
    expires_at = models.DateTimeField(help_text='When the invitation expires')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True, help_text='When the invitation was accepted')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['invited_email', 'status']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['expires_at']),
        ]
        # Allow multiple invitations per project
        # For email invitations: one per email per project (handled in view logic)
        # For shareable links: multiple allowed per project
    
    def __str__(self):
        return f"{self.project.name} - {self.invited_email} ({self.status})"
    
    def generate_token(self):
        """Generate a secure random token for the invitation"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if the invitation has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_be_accepted(self):
        """Check if the invitation can still be accepted"""
        return self.status == 'pending' and not self.is_expired()
    
    def accept(self, user=None):
        """Accept the invitation and add user to the project"""
        if not self.can_be_accepted():
            return False
        
        # For shareable links (invited_email is empty), always use the provided user
        if self.invitation_type == 'link' and user:
            self.invited_user = user
        # For email invitations, check if user matches the invited email
        elif user and user.email == self.invited_email:
            self.invited_user = user
        elif not self.invited_user and self.invited_email:
            # Try to find the user by email
            try:
                self.invited_user = User.objects.get(email=self.invited_email)
            except User.DoesNotExist:
                pass
        
        # Add user to the project's team
        if self.invited_user:
            self.project.team_toad_user.add(self.invited_user)
            self.project.is_team_toad = True
            self.project.save()
        
        # Update invitation status
        from django.utils import timezone
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        return True

# Signal to automatically add user to team_toad_user when is_team_toad is set to True
@receiver(post_save, sender=Project)
def add_user_to_team_toad(sender, instance, created, **kwargs):
    """
    Automatically add the project owner to team_toad_user when is_team_toad is set to True.
    This handles cases where the save method might not catch all scenarios.
    """
    if instance.is_team_toad and instance.user not in instance.team_toad_user.all():
        instance.team_toad_user.add(instance.user)