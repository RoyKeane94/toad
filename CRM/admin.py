from django.contrib import admin
from .models import Lead, LeadFocus, LeadMessage, SocietyLink, SocietyUniversity

# Register your models here.

admin.site.register(SocietyLink)
admin.site.register(Lead)
admin.site.register(LeadFocus)
admin.site.register(LeadMessage)
admin.site.register(SocietyUniversity)