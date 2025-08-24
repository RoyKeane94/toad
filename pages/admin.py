from django.contrib import admin

# Register your models here.

from .models import (
    Project, RowHeader, ColumnHeader, Task, PersonalTemplate, 
    TemplateRowHeader, TemplateColumnHeader, TemplateTask, ContactSubmission
)

# Basic admin registration for existing models
admin.site.register(Project)
admin.site.register(RowHeader)
admin.site.register(ColumnHeader)
admin.site.register(PersonalTemplate)
admin.site.register(TemplateRowHeader)
admin.site.register(TemplateColumnHeader)
admin.site.register(TemplateTask)

# Enhanced admin for Task model with date filtering
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'row_header', 'column_header', 'completed', 'created_at', 'updated_at']
    list_filter = [
        'completed', 
        'created_at', 
        'updated_at',
        'project__user',  # Filter by user who owns the project
        'project__project_group',  # Filter by project group
    ]
    list_editable = ['completed']
    search_fields = ['text', 'project__name', 'row_header__name', 'column_header__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'  # This adds a date drill-down navigation
    
    fieldsets = (
        ('Task Details', {
            'fields': ('text', 'completed', 'order')
        }),
        ('Relationships', {
            'fields': ('project', 'row_header', 'column_header')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries by selecting related fields"""
        return super().get_queryset(request).select_related(
            'project', 'row_header', 'column_header', 'project__user', 'project__project_group'
        )

# Enhanced admin for Contact Submissions
@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'category', 'subject', 'status', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    list_editable = ['status']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'user')
        }),
        ('Message Details', {
            'fields': ('category', 'subject', 'message', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user"""
        return super().get_queryset(request).select_related('user')