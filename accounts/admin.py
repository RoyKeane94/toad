from django.contrib import admin
from .models import User, BetaTester, UserTier
# Register your models here.

admin.site.register(User)
admin.site.register(BetaTester)
admin.site.register(UserTier)