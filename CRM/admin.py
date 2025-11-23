from django.contrib import admin
from .models import Lead, LeadFocus, LeadMessage, SocietyLink, SocietyUniversity, Company, CompanySector, ContactMethod

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
