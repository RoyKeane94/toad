from django.contrib import admin
from .models import User
# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'tier', 'email_subscribed', 'email_verified', 'is_active', 'date_joined')
    list_filter = ('email_subscribed', 'email_verified', 'tier', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('email', 'first_name', 'last_name', 'password')
        }),
        ('Account Status', {
            'fields': ('tier', 'email_verified', 'email_subscribed', 'is_active', 'account_locked_until')
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
