from django.contrib import admin

# Register your models here.

from .models import (
    Project, RowHeader, ColumnHeader, Task, PersonalTemplate, 
    TemplateRowHeader, TemplateColumnHeader, TemplateTask, FAQ, ContactSubmission
)

# Enhanced admin for Project
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at', 'updated_at', 'task_count']
    list_filter = ['user', 'created_at', 'updated_at', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['name', 'user__username', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    
    fieldsets = (
        ('Project Details', {
            'fields': ('name', 'user')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user and annotating task count"""
        from django.db.models import Count
        return super().get_queryset(request).select_related('user').annotate(
            task_count=Count('task')
        )
    
    def task_count(self, obj):
        """Display task count for each project"""
        return obj.task_count
    task_count.short_description = 'Tasks'
    task_count.admin_order_field = 'task_count'
# Enhanced admin for RowHeader
@admin.register(RowHeader)
class RowHeaderAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'order', 'task_count', 'created_at']
    list_filter = ['project', 'created_at', ('created_at', admin.DateFieldListFilter)]
    list_editable = ['order']
    search_fields = ['name', 'project__name']
    ordering = ['project', 'order']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        """Optimize queries by selecting related project and annotating task count"""
        from django.db.models import Count
        return super().get_queryset(request).select_related('project').annotate(
            task_count=Count('task')
        )
    
    def task_count(self, obj):
        """Display task count for each row"""
        return obj.task_count
    task_count.short_description = 'Tasks'
    task_count.admin_order_field = 'task_count'

# Enhanced admin for ColumnHeader
@admin.register(ColumnHeader)
class ColumnHeaderAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'order', 'task_count', 'created_at']
    list_filter = ['project', 'created_at', ('created_at', admin.DateFieldListFilter)]
    list_editable = ['order']
    search_fields = ['name', 'project__name']
    ordering = ['project', 'order']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        """Optimize queries by selecting related project and annotating task count"""
        from django.db.models import Count
        return super().get_queryset(request).select_related('project').annotate(
            task_count=Count('task')
        )
    
    def task_count(self, obj):
        """Display task count for each column"""
        return obj.task_count
    task_count.short_description = 'Tasks'
    task_count.admin_order_field = 'task_count'

# Enhanced admin for Task
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'row_header', 'column_header', 'completed', 'user', 'created_at', 'updated_at']
    list_filter = [
        'completed', 
        'user', 
        'project', 
        'created_at', 
        'updated_at',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ]
    list_editable = ['completed']
    search_fields = ['text', 'project__name', 'row_header__name', 'column_header__name']
    ordering = ['-created_at', 'order']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    
    fieldsets = (
        ('Task Details', {
            'fields': ('text', 'completed', 'order', 'user')
        }),
        ('Grid Position', {
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
            'user', 'project', 'row_header', 'column_header'
        ).prefetch_related(
            'project__user'
        )

admin.site.register(PersonalTemplate)
admin.site.register(TemplateRowHeader)
admin.site.register(TemplateColumnHeader)
admin.site.register(TemplateTask)

# Enhanced admin for FAQ
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    search_fields = ['question', 'answer']
    ordering = ['category', 'order', 'question']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('question', 'answer', 'category', 'order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
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