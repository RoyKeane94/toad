from django.contrib import admin

from .models import MCPRequestLog, PersonalAccessToken, TaskActivity


@admin.register(PersonalAccessToken)
class PersonalAccessTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'token_prefix', 'created_at', 'last_used_at')
    search_fields = ('user__email', 'token_prefix', 'name')
    readonly_fields = ('user', 'token_prefix', 'token_hash', 'created_at', 'last_used_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False


@admin.register(MCPRequestLog)
class MCPRequestLogAdmin(admin.ModelAdmin):
    list_display = ('asked_by', 'user', 'follow_up_needed', 'created_at')
    list_filter = ('follow_up_needed', 'created_at')
    search_fields = ('asked_by', 'request_text', 'user__email')
    readonly_fields = ('user', 'asked_by', 'request_text', 'follow_up_needed', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ('agent', 'action', 'task_text', 'created_at', 'user')
    list_filter = ('action', 'created_at')
    search_fields = ('agent', 'action', 'task_text', 'user__email')
    readonly_fields = (
        'user', 'project', 'task', 'agent', 'action', 'task_text', 'created_at',
    )
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False
