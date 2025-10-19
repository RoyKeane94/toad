from django.contrib import admin
from .models import User
# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'tier', 'associated_university', 'trial_status', 'email_subscribed', 'email_verified', 'is_active', 'date_joined')
    list_filter = ('email_subscribed', 'email_verified', 'tier', 'associated_university', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'associated_university__name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'trial_status')
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('email', 'first_name', 'last_name', 'password')
        }),
        ('Account Status', {
            'fields': ('tier', 'email_verified', 'email_subscribed', 'is_active', 'account_locked_until')
        }),
        ('University & Society', {
            'fields': ('associated_university', 'associated_society'),
            'classes': ('collapse',)
        }),
        ('Trial Information', {
            'fields': ('trial_status', 'trial_started_at', 'trial_ends_at'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
