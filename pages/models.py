from django.db import models
from accounts.models import User  # Use our custom User model
from django.urls import reverse

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='toad_projects')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('project_grid', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),  # For user's project list
            models.Index(fields=['user', 'id']),  # For project access checks
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:50] if self.text else 'Empty Task'
    
    def clean(self):
        if not self.text or not self.text.strip():
            from django.core.exceptions import ValidationError
            raise ValidationError({'text': 'Task text cannot be empty.'})

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['project', 'row_header', 'column_header']),  # For cell-based task queries
            models.Index(fields=['project', 'completed']),  # For completed task filtering
            models.Index(fields=['project', 'created_at']),  # For task ordering
        ]

class Template(models.Model):
    CATEGORY_CHOICES = [
        ('student', 'Student'),
        ('professional', 'Professional'),
        ('personal', 'Personal'),
        ('event', 'Event'),
        ('everyday', 'Everyday'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['category', 'name']


class TemplateRowHeader(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='row_headers')
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
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='column_headers')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['template', 'order']

    def __str__(self):
        return f"{self.template.name} - {self.name}"
    
    