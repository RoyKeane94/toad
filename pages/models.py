from django.db import models
from accounts.models import User  # Use our custom User model
from django.urls import reverse

class ProjectGroup(models.Model):
    name = models.CharField(max_length=100)
    is_team_toad = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
    
class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='toad_projects')
    name = models.CharField(max_length=100)
    is_team_toad = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)  # For maintaining project order within groups
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('project_grid', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['project_group', 'order', '-created_at']  # Order by group, then by order, then by creation time
        indexes = [
            models.Index(fields=['user', '-created_at']),  # For user's project list
            models.Index(fields=['user', 'id']),  # For project access checks
            models.Index(fields=['user', 'project_group', 'order']),  # For ordered project queries within groups
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

class PersonalTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_templates')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

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


    