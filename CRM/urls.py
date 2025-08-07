from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.crm_home, name='home'),
    # Add more CRM-specific URLs here as needed
]
