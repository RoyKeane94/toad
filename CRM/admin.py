from django.contrib import admin
from .models import Lead, LeadFocus, LeadMessage, SocietyLink, SocietyUniversity, Feedback, Company, CompanySector, ContactMethod

# Register your models here.

# Society-related models
admin.site.register(SocietyLink)
admin.site.register(SocietyUniversity)

# B2B-related models
admin.site.register(Company)
admin.site.register(CompanySector)
# Shared models
admin.site.register(Lead)
admin.site.register(LeadFocus)
admin.site.register(ContactMethod)
admin.site.register(LeadMessage)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_display', 'regularly_using_toad', 'would_share', 'created_at']
    list_filter = ['regularly_using_toad', 'would_share', 'organization_method', 'created_at']
    search_fields = ['name', 'usage_reason', 'user__email']
    readonly_fields = ['created_at', 'ip_address']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name', 'ip_address', 'created_at')
        }),
        ('Core Feedback', {
            'fields': ('regularly_using_toad', 'usage_reason')
        }),
        ('Organization', {
            'fields': ('organization_method', 'organization_other')
        }),
        ('Improvement Suggestions', {
            'fields': ('non_user_suggestion', 'user_improvement')
        }),
        ('Team Toad & Sharing', {
            'fields': ('team_toad_interest', 'would_share')
        }),
    )
    
    def get_user_display(self, obj):
        if obj.user:
            return obj.user.email
        elif obj.name:
            return obj.name
        return 'Anonymous'
    get_user_display.short_description = 'User'
    get_user_display.admin_order_field = 'user'