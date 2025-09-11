from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.crm_home, name='home'),
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/create/', views.lead_create, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/update/', views.lead_update, name='lead_update'),
    path('leads/<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('leads/<int:lead_pk>/messages/create/', views.lead_message_create, name='lead_message_create'),
    path('focus/create/', views.lead_focus_create, name='lead_focus_create'),
    path('contact-methods/create/', views.contact_method_create, name='contact_method_create'),
    
    # Society Links
    path('society-links/', views.society_link_list, name='society_link_list'),
    path('society-links/create/', views.society_link_create, name='society_link_create'),
    path('society-links/<int:pk>/delete/', views.society_link_delete, name='society_link_delete'),
    path('society-universities/create/', views.society_university_create, name='society_university_create'),
    path('<str:university_slug>/<str:society_slug>/', views.society_link_public, name='society_link_public'),
    path('<str:university_slug>/<str:society_slug>/qr/', views.society_link_public_qr, name='society_link_public_qr'),
    path('<str:university_slug>/<str:society_slug>/qr-image/', views.society_link_qr_image, name='society_link_qr_image'),
    # Fallback for old format (temporary)
    path('society-links/<int:pk>/public/', views.society_link_public_old, name='society_link_public_old'),
    
]
