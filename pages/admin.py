from django.contrib import admin

# Register your models here.

from .models import (
    Project, RowHeader, ColumnHeader, Task, Template, 
    TemplateRowHeader, TemplateColumnHeader, FAQ, ContactSubmission
)

# Basic admin registration for existing models
admin.site.register(Project)
admin.site.register(RowHeader)
admin.site.register(ColumnHeader)
admin.site.register(Task)
admin.site.register(Template)
admin.site.register(TemplateRowHeader)
admin.site.register(TemplateColumnHeader)

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