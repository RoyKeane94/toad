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

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    row_header = models.ForeignKey(RowHeader, on_delete=models.CASCADE, related_name='tasks')
    column_header = models.ForeignKey(ColumnHeader, on_delete=models.CASCADE, related_name='tasks')
    text = models.TextField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text[:50]

    class Meta:
        ordering = ['created_at']